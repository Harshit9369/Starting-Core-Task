# YouTube Influencer Campaign Manager

This project is designed to help manage and analyze YouTube influencer campaigns. It fetches data from YouTube influencers using the RapidAPI service and provides tools to store and visualize the data in a PostgreSQL database.

## Setup

To get started with this project, follow the steps below:

### 1. Create a Virtual Environment

First, create a virtual environment for your project. This will help to isolate dependencies and avoid conflicts with other Python projects.

```bash
python -m venv env
```
### 2. Activate the Virtual Environment:

On Windows:
```bash
.\env\Scripts\activate
```
On macOS/Linux:
```bash
source env/bin/activate
```

### 3. Install Dependencies:

```bash
cd env
pip install -r requirements.txt
```

### 4. Configuration

To configure the application, create a `config.py` file in the project directory. This file will store your PostgreSQL database details and API details.

### Example `config.py`:

```python
DB_CONFIG = {
    "dbname": "your_db_name",
    "user": "your_db_user",
    "password": "your_db_password",
    "host": "your_db_host",
    "port": "your_db_port"
}

API_CONFIG = {
    "url": "https://youtube-influencer-search.p.rapidapi.com/searches/100/results",
    "key": "your_api_key",
    "host": "your_api_host"
}
```
#### Note: 
The url should be modified for different search results. For example, 'url': 'https://youtube-influencer-search.p.rapidapi.com/searches/100/results', where the 100 should be replaced by other higher or lower numbers that will lead to different search results and hence more data.

### 5. Starting Application:

```bash
streamlit run app.py
```


