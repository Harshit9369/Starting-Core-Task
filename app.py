import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import requests
from config import DB_CONFIG, API_CONFIG
import time

def connect_db():
    try:
        conn = psycopg2.connect(
            dbname=DB_CONFIG['dbname'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port']
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to the database: {e}")
        return None

def get_influencers(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT channel_title, subscribers_count, views_count, video_count, country FROM influencers;")
        rows = cur.fetchall()
        cur.close()

        if rows:
            rows = replace_none_with_defaults(rows)
        
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        return []

def replace_none_with_defaults(data):
    default_values = {
        'subscribers_count': 0,
        'views_count': 0,
        'video_count': 0,
        'country': 'Unknown'
    }
    return [
        [item if item is not None else default_values.get(column_name, 'Unknown')
        for column_name, item in zip(['channel_title', 'subscribers_count', 'views_count', 'video_count', 'country'], row)]
        for row in data
    ]

def get_connections(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM connections;")
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        return []

def add_connection(conn, influencer_id, campaign_id, contact_date, status):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO connections (influencer_id, campaign_id, contact_date, status) VALUES (%s, %s, %s, %s)",
            (influencer_id, campaign_id, contact_date, status)
        )
        conn.commit()
        cur.close()
        st.success("Connection added successfully.")
    except Exception as e:
        st.error(f"Failed to add connection: {e}")

def update_connection(conn, id, contact_date, status):
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE connections SET contact_date = %s, status = %s WHERE id = %s",
            (contact_date, status, id)
        )
        conn.commit()
        cur.close()
        st.success("Connection updated successfully.")
    except Exception as e:
        st.error(f"Failed to update connection: {e}")

def delete_connection(conn, id):
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM connections WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        st.success("Connection deleted successfully.")
    except Exception as e:
        st.error(f"Failed to delete connection: {e}")

def get_campaigns(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, campaign_name, start_date, end_date FROM campaigns;")
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve campaigns: {e}")
        return []

def add_campaign(conn, name, start_date, end_date):
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO campaigns (campaign_name, start_date, end_date) VALUES (%s, %s, %s)",
            (name, start_date, end_date)
        )
        conn.commit()
        cur.close()
        st.success("Campaign added successfully.")
    except Exception as e:
        st.error(f"Failed to add campaign: {e}")

def get_connections_summary(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT c.campaign_name, COUNT(co.id) as num_connections
            FROM connections co
            JOIN campaigns c ON co.campaign_id = c.id
            GROUP BY c.campaign_name
        """)
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve connections summary: {e}")
        return []

def fetch_youtube_data():
    try:
        headers = {
            'X-RapidAPI-Key': API_CONFIG['key'],
            'X-RapidAPI-Host': API_CONFIG['host']
        }
        response = requests.get(API_CONFIG['url'], headers=headers)
        response.raise_for_status()
        youtube_data = response.json()

        filtered_data = []

        for item in youtube_data:
            data = list(item.values())

            filtered_entry = {
                "Channel Title": data[3],
                "Subscribers": data[5],
                "Views": data[6],
                "Videos": data[7],
                "Country": data[8]
            }

            filtered_data.append(filtered_entry)
        
        return filtered_data

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 429:
            st.warning("Rate limit exceeded. Please try again later.")
            time.sleep(60)
        else:
            st.error(f"Failed to fetch YouTube data: {err}")
        return []

def store_youtube_data(conn, data):
    try:
        cur = conn.cursor()
        for item in data:
            channel_title = item.get('Channel Title', 'Unknown')
            subscribers_count = item.get('Subscribers', 0)
            views_count = item.get('Views', 0)
            video_count = item.get('Videos', 0)
            country = item.get('Country', 'Unknown')

            channel_id = generate_channel_id(channel_title)

            cur.execute(
                "INSERT INTO influencers (channel_id, channel_title, subscribers_count, views_count, video_count, country) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (channel_id, channel_title, subscribers_count, views_count, video_count, country)
            )

        conn.commit()
        cur.close()
        st.success("YouTube data stored successfully.")
    except Exception as e:
        st.error(f"Failed to store YouTube data: {e}")

def generate_channel_id(channel_title):
    return hash(channel_title)

def get_influencer_campaign_data(conn):
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT i.channel_title, c.campaign_name
            FROM connections co
            JOIN influencers i ON co.influencer_id::text = i.channel_id
            JOIN campaigns c ON co.campaign_id = c.id
        """)
        rows = cur.fetchall()
        cur.close()
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve influencer-campaign data: {e}")
        return []

def main():
    st.sidebar.title("Influencer Campaign Dashboard")
    st.sidebar.markdown("[Home](#)")
    st.sidebar.markdown("[Influencers](#influencers)")
    st.sidebar.markdown("[Connections](#connections)")
    st.sidebar.markdown("[Campaigns](#campaigns)")
    
    st.title("Influencer Campaign Dashboard")
    
    conn = connect_db()
    if conn:
        st.header("Fetch YouTube Data")
        if st.button("Fetch and Store YouTube Data"):
            youtube_data = fetch_youtube_data()
            if youtube_data:
                store_youtube_data(conn, youtube_data)
        
        st.header("Influencers")
        influencers = get_influencers(conn)
        if influencers:
            df = pd.DataFrame(influencers, columns=['Channel Title', 'Subscribers', 'Views', 'Videos', 'Country'])
            df['Subscribers'] = df['Subscribers'].astype(int)
            df['Views'] = df['Views'].astype(int)
            df['Videos'] = df['Videos'].astype(int)
            st.dataframe(df)
        else:
            st.write("No influencer data available.")
        
        st.header("Existing Connections")
        connections = get_connections(conn)
        if connections:
            df_conn = pd.DataFrame(connections, columns=['ID', 'Influencer ID', 'Campaign ID', 'Contact Date', 'Status'])
            st.dataframe(df_conn)
        else:
            st.write("No connections available.")

        st.header("Add a New Connection")
        with st.form("add_connection_form"):
            influencer_id = st.number_input("Influencer ID", min_value=1)
            campaign_id = st.number_input("Campaign ID", min_value=1)
            contact_date = st.date_input("Contact Date")
            status = st.selectbox("Status", ["Not Contacted", "Contacted", "Interested", "Not Responded"])
            submit_button = st.form_submit_button("Add Connection")
            if submit_button:
                add_connection(conn, influencer_id, campaign_id, contact_date, status)

        st.header("Update a Connection")
        with st.form("update_connection_form"):
            id = st.number_input("Connection ID", min_value=1)
            contact_date = st.date_input("New Contact Date")
            status = st.selectbox("New Status", ["Not Contacted", "Contacted", "Interested", "Not Responded"])
            update_button = st.form_submit_button("Update Connection")
            if update_button:
                update_connection(conn, id, contact_date, status)

        st.header("Delete a Connection")
        with st.form("delete_connection_form"):
            id = st.number_input("Connection ID to Delete", min_value=1)
            delete_button = st.form_submit_button("Delete Connection")
            if delete_button:
                delete_connection(conn, id)
        
        st.header("Campaigns")
        campaigns = get_campaigns(conn)
        if campaigns:
            df_camp = pd.DataFrame(campaigns, columns=['ID', 'Campaign Name', 'Start Date', 'End Date'])
            st.dataframe(df_camp)
        else:
            st.write("No campaigns available.")

        st.header("Add a New Campaign")
        with st.form("add_campaign_form"):
            name = st.text_input("Campaign Name")
            start_date = st.date_input("Start Date")
            end_date = st.date_input("End Date")
            add_campaign_button = st.form_submit_button("Add Campaign")
            if add_campaign_button:
                add_campaign(conn, name, start_date, end_date)

        st.header("Connections Summary")
        connections_summary = get_connections_summary(conn)
        if connections_summary:
            df_summary = pd.DataFrame(connections_summary, columns=['Campaign Name', 'Number of Connections'])
            fig = px.bar(df_summary, x='Campaign Name', y='Number of Connections')
            st.plotly_chart(fig)
        else:
            st.write("No connection summary available.")

        conn.close()

if __name__ == "__main__":
    main()