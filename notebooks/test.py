from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import ibm_db_dbi
import pandas as pd
from typing import List, Optional
from datetime import datetime
from sqlalchemy import create_engine
import numpy as np
import re

app = FastAPI()


def create_dataframe(data, username, now):

    # Convert the list to a dataframe
    df = pd.DataFrame(data)

    # Drop the 'n' column if it exists
    if "n" in df.columns:
        df = df.drop(columns=["n"])

    # Rename columns
    df = df.rename(columns={"a": "Input", "u": "Output"})

    # Append new columns
    df["name"] = np.nan
    df["time"] = np.nan

    # Fill the first row with the provided name and timestamp
    df.loc[0, "name"] = username
    df.loc[0, "time"] = now
    return df


def create_datafram_string(data, username, now):
    # Define pattern for extracting key-value pairs
    pattern = r'\{"([au])":"(.*?)"(?:,"[nu]":true)?}'

    # Extract matches using regex
    matches = re.findall(pattern, data, re.DOTALL)

    # Create dictionary from matches
    result_dict = {}
    for match in matches:
        key = match[0]
        value = match[1]
        if key not in result_dict:
            result_dict[key] = []
        result_dict[key].append(value)

    # print(result_dict)
    # Find the maximum length of lists in the dictionary
    max_length = max(len(lst) for lst in result_dict.values())

    # Pad lists with NaN where necessary
    for key in result_dict:
        result_dict[key] += [np.nan] * (max_length - len(result_dict[key]))

    # Create dataframe
    df = pd.DataFrame(result_dict)
    # Rename columns
    df = df.rename(columns={"a": "input_text", "u": "output_text"})

    # Append new columns
    df["user_name"] = np.nan
    df["created_ts"] = np.nan

    # Fill the first row with the provided name and timestamp
    df.loc[0, "user_name"] = username
    df.loc[0, "created_ts"] = now

    columns_to_replace = ["user_name", "created_ts"]

    for column in columns_to_replace:
        df[column].fillna(df[column].iloc[0], inplace=True)

    return df


@app.post("/insert_data")
def insert_data(
    dsn_database: str = Query(..., description="Database name"),
    dsn_hostname: str = Query(..., description="Hostname"),
    dsn_port: int = Query(..., description="Port"),
    dsn_uid: str = Query(..., description="User ID"),
    dsn_pwd: str = Query(..., description="Password"),
    data: Optional[str] = Query(..., description="DataToInsert"),
    username: Optional[str] = Query(..., description="User name"),
):
    # Create the connection string
    dsn = (
        f"DATABASE={dsn_database};"
        f"HOSTNAME={dsn_hostname};"
        f"PORT={dsn_port};"
        f"PROTOCOL=TCPIP;"
        f"UID={dsn_uid};"
        f"PWD={dsn_pwd};"
        f"SECURITY=SSL;"
    )

    # Establish the connection
    try:
        print("Before connection call")
        conn = ibm_db_dbi.connect(dsn, "", "")
        cursor = conn.cursor()
        print("Connected to the database")
    except Exception as e:
        print("Unable to connect to the database")
        raise HTTPException(
            status_code=500, detail=f"Unable to connect to the database: {str(e)}"
        )

    try:
        now = datetime.now()
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        insert_query = (
            "INSERT INTO development.watsonx_chat_table (created_ts, user_name, input_text, output_text)"
            "VALUES (?, ?, ?, ?)"
        )
        df = create_datafram_string(data, username, formatted_now)

        # conn_str = f'ibm_db_sa://{dsn_uid}:{dsn_pwd}@{dsn_hostname}:{dsn_port}/{dsn_database}'
        # engine = create_engine(conn_str)

        # table_name = "development.watsonx_chat_table"
        # df.to_sql(table_name, engine, if_exists='append', index=False)

        for index, row in df.iterrows():
            # print(index, type(pd.to_datetime(row['created_ts'])), type(str(row['user_name'])), type(str(row['input_text'])), type(str(row['output_text'])))
            cursor.execute(
                insert_query,
                (
                    pd.to_datetime(row["created_ts"]),
                    str(row["user_name"]),
                    str(row["input_text"]),
                    str(row["output_text"]),
                ),
            )

        conn.commit()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unable to insert data: {str(e)}")
    finally:
        # Close the connection
        if conn:
            conn.close()
            print("Connection closed")

    return {"detail": "Response captured successfully"}
