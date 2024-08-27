import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from config import API_CONFIG
import time
import psycopg2

def init_connection():
    conn = psycopg2.connect(
        dbname=st.secrets["db_name"],
        user=st.secrets["user"],
        password=st.secrets["password"],
        host=st.secrets["host"],
        port=st.secrets["port"]
    )
    return conn

def execute_query(query, params=None):
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        if query.strip().lower().startswith('select'):
            return cursor.fetchall()
        conn.commit()


def get_influencers():
    try:
        query = "SELECT channel_title, subscribers_count, views_count, video_count, country FROM influencers;"
        rows = conn.query(query, ttl="10m")
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

def get_connections():
    try:
        query = "SELECT * FROM connections;"
        rows = conn.query(query, ttl="10m")
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve data: {e}")
        return []

def add_connection(influencer_id, campaign_id, contact_date, status):
    query = """
        INSERT INTO connections (influencer_id, campaign_id, contact_date, status)
        VALUES (%s, %s, %s, %s)
    """
    execute_query(query, (influencer_id, campaign_id, contact_date, status))
    st.success("Connection added successfully.")


def update_connection(id, contact_date, status):
    try:
        query = """
            UPDATE connections SET contact_date = %s, status = %s WHERE id = %s
        """
        conn.query(query, params=(contact_date, status, id))
        st.success("Connection updated successfully.")
    except Exception as e:
        st.error(f"Failed to update connection: {e}")

def delete_connection(id):
    try:
        query = "DELETE FROM connections WHERE id = %s"
        conn.query(query, params=(id,))
        st.success("Connection deleted successfully.")
    except Exception as e:
        st.error(f"Failed to delete connection: {e}")

def get_campaigns():
    try:
        query = "SELECT id, campaign_name, start_date, end_date FROM campaigns;"
        rows = conn.query(query, ttl="10m")
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve campaigns: {e}")
        return []

def add_campaign(name, start_date, end_date):
    try:
        query = """
            INSERT INTO campaigns (campaign_name, start_date, end_date)
            VALUES (%s, %s, %s)
        """
        conn.query(query, params=(name, start_date, end_date))
        st.success("Campaign added successfully.")
    except Exception as e:
        st.error(f"Failed to add campaign: {e}")

def get_connections_summary():
    try:
        query = """
            SELECT c.campaign_name, COUNT(co.id) as num_connections
            FROM connections co
            JOIN campaigns c ON co.campaign_id = c.id
            GROUP BY c.campaign_name
        """
        rows = conn.query(query, ttl="10m")
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

def store_youtube_data(data):
    try:
        for item in data:
            channel_title = item.get('Channel Title', 'Unknown')
            subscribers_count = item.get('Subscribers', 0)
            views_count = item.get('Views', 0)
            video_count = item.get('Videos', 0)
            country = item.get('Country', 'Unknown')

            channel_id = generate_channel_id(channel_title)

            query = """
                INSERT INTO influencers (channel_id, channel_title, subscribers_count, views_count, video_count, country)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            conn.query(query, params=(channel_id, channel_title, subscribers_count, views_count, video_count, country))

        st.success("YouTube data stored successfully.")
    except Exception as e:
        st.error(f"Failed to store YouTube data: {e}")

def generate_channel_id(channel_title):
    return hash(channel_title)

def get_influencer_campaign_data():
    try:
        query = """
            SELECT i.channel_title, c.campaign_name
            FROM connections co
            JOIN influencers i ON co.influencer_id::text = i.channel_id
            JOIN campaigns c ON co.campaign_id = c.id
        """
        rows = conn.query(query, ttl="10m")
        return rows
    except Exception as e:
        st.error(f"Failed to retrieve influencer-campaign data: {e}")
        return []

def main():
    global conn
    st.sidebar.title("Influencer Campaign Dashboard")
    st.sidebar.markdown("[Home](#)")
    st.sidebar.markdown("[Influencers](#influencers)")
    st.sidebar.markdown("[Connections](#connections)")
    st.sidebar.markdown("[Campaigns](#campaigns)")
    
    st.title("Influencer Campaign Dashboard")

    st.header("Fetch YouTube Data")
    if st.button("Fetch and Store YouTube Data"):
        youtube_data = fetch_youtube_data()
        if youtube_data:
            store_youtube_data(youtube_data)

    st.header("Influencers")
    influencers = get_influencers()
    if influencers:
        df = pd.DataFrame(influencers, columns=['Channel Title', 'Subscribers', 'Views', 'Videos', 'Country'])
        df['Subscribers'] = df['Subscribers'].astype(int)
        df['Views'] = df['Views'].astype(int)
        df['Videos'] = df['Videos'].astype(int)
        st.dataframe(df)
    else:
        st.write("No influencer data available.")

    st.header("Existing Connections")
    connections = get_connections()
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
            add_connection(influencer_id, campaign_id, contact_date, status)

    st.header("Update a Connection")
    with st.form("update_connection_form"):
        id = st.number_input("Connection ID", min_value=1)
        contact_date = st.date_input("New Contact Date")
        status = st.selectbox("New Status", ["Not Contacted", "Contacted", "Interested", "Not Responded"])
        update_button = st.form_submit_button("Update Connection")
        if update_button:
            update_connection(id, contact_date, status)

    st.header("Delete a Connection")
    with st.form("delete_connection_form"):
        id = st.number_input("Connection ID to Delete", min_value=1)
        delete_button = st.form_submit_button("Delete Connection")
        if delete_button:
            delete_connection(id)
        
    st.header("Campaigns")
    campaigns = get_campaigns()
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
            add_campaign(name, start_date, end_date)

    st.header("Connections Summary")
    connections_summary = get_connections_summary()
    if connections_summary:
        df_summary = pd.DataFrame(connections_summary, columns=['Campaign Name', 'Number of Connections'])
        fig = px.bar(df_summary, x='Campaign Name', y='Number of Connections')
        st.plotly_chart(fig)
    else:
        st.write("No connection summary available.")

    conn.close()

if __name__ == "__main__":
    main()