import numpy as np
import streamlit as st
import openpyxl
import pandas as pd
from random import randrange

# This is for the social graph drawing
from pyvis import network as net

# Constants: Row & Column indexes for the microblog social graph file
NAMES_COL = 0
NAMES_ROW = 0
HANDLES_COL = 2  # Remember columns start numbering at 0 in Python
FACTIONS_COL = 3

# Start to create the network viz
g = net.Network(height='1025px', width='50%', heading='', directed=True)
g.set_options('''
var options = {
    "nodes": {
        "borderWidth": 1,
        "borderWidthSelected": 8
    },
    "edges": {
        "borderWidthSelected": 8
    },
    "physics": {
        "barnesHut": {
            "gravitationalConstant": -14900,
            "centralGravity": 2.2,
            "springLength": 110,
            "springConstant": 0.001
        },
        "minVelocity": 0.75,
        "timestep": 0.46
    }
}
''')


# This looks overall likely to follow based on reach
def whats_the_friendship(a, b, attraction_df, affinity_df):
    # Get the persona factions
    if a not in attraction_df.TwHandle.values:
        st.write(f"Handle {a} not found in attraction_df")
        return 0, 0

    if b not in attraction_df.TwHandle.values:
        st.write(f"Handle {b} not found in attraction_df")
        return 0, 0

    faction_a = attraction_df.loc[attraction_df.TwHandle == a, "Faction"].values[0]
    faction_b = attraction_df.loc[attraction_df.TwHandle == b, "Faction"].values[0]
    try:
        affinity_between_factions = affinity_df.loc[(affinity_df.Faction == faction_a) & (affinity_df.Other_Faction == faction_b), "Affinity"].values[0]
    except:
        affinity_between_factions = 0

    # FIRST pass "a is followed by b?"
    if faction_a == faction_b:  # Need to use the "inter-faction affinity"
        likelihood_of_following = attraction_df.loc[attraction_df.TwHandle == a, "Prob4Faction"].values[0]
        affinity_between_factions = 1  # This overrides the "0" from above
        # Small fiddle
        # I found that in small samples the inter-faction wasn't high enough for my liking :)
        # Therefore I'm bumping up the likelihood to get chance of more followers
        followers = attraction_df.loc[attraction_df.TwHandle == a, "TwFollowers"].values[0]
        if followers > 5000 and followers < 10000:
            st.write(a)
            st.write(likelihood_of_following)
            likelihood_of_following = likelihood_of_following + 0.2
        if followers < 1000:
            likelihood_of_following = likelihood_of_following - 0.1
    else:
        # If they're different factions then the likelihood of following is based on the persona's reach * affinity between the factions (i.e. reduced if unlikely)
        likelihood_of_following = attraction_df.loc[attraction_df.TwHandle == a, "ProbOverAll"].values[0] * affinity_between_factions

    dice_roll = randrange(100) / 100
    if likelihood_of_following > dice_roll:  # Then b is following a
        x = 3
    else:
        x = 0

    # SECOND pass "b is followed by a?"
    if faction_a == faction_b:  # Need to use the "inter-faction affinity"
        likelihood_of_following = attraction_df.loc[attraction_df.TwHandle == b, "Prob4Faction"].values[0]
        affinity_between_factions = 1  # This overrides the "0" from above
        # Small fiddle
        # I found that in small samples the inter-faction wasn't high enough for my liking :)
        # Therefore I'm bumping up the likelihood to get chance of more followers
        followers = attraction_df.loc[attraction_df.TwHandle == b, "TwFollowers"].values[0]
        if followers > 5000 and followers < 10000:
            st.write(b)
            st.write(likelihood_of_following)
            likelihood_of_following = likelihood_of_following + 0.2
        if followers < 1000:
            likelihood_of_following = likelihood_of_following - 0.1
    else:
        # If they're different factions then the likelihood of following is based on the persona's reach * affinity between the factions (i.e. reduced if unlikely)
        likelihood_of_following = attraction_df.loc[attraction_df.TwHandle == b, "ProbOverAll"].values[0] * affinity_between_factions

    dice_roll = randrange(100) / 100
    if likelihood_of_following > dice_roll:  # Then b is following a
        y = 1
    else:
        y = 0

    # If they follow each other then it's a 2!
    if x == 1 and y == 3:
        x = 2
        y = 2

    return x, y


# Input fields for file uploads
st.title("Microblog Social Graph")

persona_details = st.file_uploader("Upload persona_details.xlsx", type=["xlsx"])
social_graph = st.file_uploader("Upload Microblog_social_graph.xlsx", type=["xlsx"])

if persona_details and social_graph:
    df = pd.read_excel(persona_details)
    df2 = df[["Faction", "TwFollowers", "TwHandle", "TwBio"]]
    df2 = df2.sort_values(["Faction", "TwFollowers"], ascending=False).groupby("Faction").head(1000)
    st.write(df2)
    df2["Prob4Faction"] = df2["TwFollowers"] / df2.groupby("Faction")["TwFollowers"].transform("sum")
    df2["ProbOverAll"] = df2["TwFollowers"] / df2["TwFollowers"].sum()
    st.write(df2)
    attraction_df = df2

    source_wb = openpyxl.load_workbook(social_graph)
    social_graph_sheet = source_wb.active
    max_rows = social_graph_sheet.max_row

    handles = [social_graph_sheet.cell(row=i, column=HANDLES_COL + 1).value for i in range(2, max_rows + 1)]

    factions = [social_graph_sheet.cell(row=i, column=FACTIONS_COL + 1).value for i in range(2, max_rows + 1)]
    factions = list(dict.fromkeys(factions))
    factions.remove("Faction")
    #factions.remove("")
    st.write(factions)

    factions_df = pd.DataFrame(factions, columns=["Faction"])
    factions_df["Other_Faction"] = ""
    factions_df["Affinity"] = 0
    st.write(factions_df)

    st.write("Please edit the faction affinity below and then save:")
    affinity_file = st.file_uploader("Upload Faction affinity file", type=["xlsx"])
    if affinity_file:
        affinity_df = pd.read_excel(affinity_file)
        affinity_df = affinity_df[["Faction", "Other_Faction", "Affinity"]]
        st.table(affinity_df)

        for i in range(1, max_rows):
            persona = handles[i - 1]
            bio = df2.loc[df2.TwHandle == persona, "TwBio"].values[0] if not df2.loc[df2.TwHandle == persona, "TwBio"].empty else ""
            faction = df2.loc[df2.TwHandle == persona, "Faction"].values[0] if not df2.loc[df2.TwHandle == persona, "Faction"].empty else ""

            try:
                g.add_node(persona, title="(" + persona + ")[" + faction + "] " + bio)
            except:
                g.add_node(persona, title="(" + persona + ")[" + faction + "] ")

        for i in range(2, len(handles) + 1):
            for j in range(i + 1, len(handles) + 1):
                followed = handles[i - 1]
                follower = handles[j - 1]

                friend_value_x, friend_value_y = whats_the_friendship(followed, follower, attraction_df, affinity_df)

                if friend_value_x > 0:
                    g.add_edge(follower, followed)
                    social_graph_sheet.cell(row=i, column=j + 2, value=friend_value_x)
                elif friend_value_y > 0:
                    g.add_edge(followed, follower)
                    social_graph_sheet.cell(row=i, column=j + 2, value=friend_value_y)

        output_path = 'social_OUTPUT.xlsx'
        source_wb.save(output_path)
        st.write("Social graph processing complete. Download the updated social graph:")
        st.download_button(label="Download social_OUTPUT.xlsx", data=open(output_path, 'rb').read(), file_name=output_path)

        g.save_graph('networkviz.html')
        HtmlFile = open("networkviz.html", 'r', encoding='utf-8')
        source_code = HtmlFile.read()
        st.components.v1.html(source_code, height=800)

    st.header("All Done!")
