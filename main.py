import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Function to fetch vegetable prices (with caching)
@st.cache_data
def fetch_vegetable_prices(city):
    """
    Fetches vegetable prices for the given city and returns a DataFrame.
    """
    url = f"https://vegetablemarketprice.com/market/{city}/today"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    # Check if the response is valid
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch data for {city}. Status code: {response.status_code}")

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table")

    # Validate table existence
    if table is None:
        raise ValueError("No data table found on the page.")

    # Parse table rows into a list of dictionaries
    rows = [
        {
            "Vegetable": row.find_all("td")[1].text.strip(),
            "Min Price (₹)": float(row.find_all("td")[3].text.strip().replace("₹", "").split(" - ")[0]),
            "Max Price (₹)": float(row.find_all("td")[3].text.strip().replace("₹", "").split(" - ")[1]),
        }
        for row in table.find_all("tr")[1:]  # Skip header
        if len(row.find_all("td")) >= 4  # Ensure valid row structure
    ]

    # Convert to DataFrame
    df = pd.DataFrame(rows)
    df["Avg Price (₹)"] = (df["Min Price (₹)"] + df["Max Price (₹)"]) / 2
    df.set_index("Vegetable", inplace=True)
    return df

# Streamlit App
st.title("Vegetable Calculator")

# Step 1: Allow user to select the city
city = st.text_input("Enter the city:", "ahmedabad").lower().strip()

# Step 2: Fetch the DataFrame based on the city (cached)
try:
    if city:
        df = fetch_vegetable_prices(city)
        st.write(f"### Current Vegetable Prices in {city.capitalize()}:")
        st.dataframe(df)
except Exception as e:
    st.error(f"Failed to fetch data: {e}")
    st.stop()

# Step 3: Inputs for vegetable and quantity
st.write("### Add Vegetables to Your Bill")
selected_vegetable = st.selectbox("Select a vegetable:", df.index)
quantity = st.number_input("Enter quantity (in kg):", min_value=0.0, step=0.1)

# Initialize bill storage if not present
if "bill" not in st.session_state:
    st.session_state["bill"] = pd.DataFrame(columns=["Vegetable", "Quantity (kg)", "Min Price (₹)", "Max Price (₹)", "Avg Price (₹)"])

# Add vegetable to the bill
if st.button("Add to Bill"):
    if selected_vegetable and quantity > 0:
        new_entry = {
            "Vegetable": selected_vegetable,
            "Quantity (kg)": quantity,
            "Min Price (₹)": df.loc[selected_vegetable, "Min Price (₹)"] * quantity,
            "Max Price (₹)": df.loc[selected_vegetable, "Max Price (₹)"] * quantity,
            "Avg Price (₹)": df.loc[selected_vegetable, "Avg Price (₹)"] * quantity,
        }
        st.session_state["bill"] = pd.concat([st.session_state["bill"], pd.DataFrame([new_entry])], ignore_index=True)
        st.success(f"Added {quantity} kg of {selected_vegetable} to the bill.")
    else:
        st.error("Please select a vegetable and enter a valid quantity.")

# Step 4: Display the bill
if not st.session_state["bill"].empty:
    # Calculate totals
    totals = st.session_state["bill"].sum(numeric_only=True)
    totals_row = {
        "Vegetable": "Total",
        "Quantity (kg)": "",
        "Min Price (₹)": totals["Min Price (₹)"],
        "Max Price (₹)": totals["Max Price (₹)"],
        "Avg Price (₹)": totals["Avg Price (₹)"],
    }

    # Add totals as the last row in the DataFrame
    bill_with_totals = pd.concat([st.session_state["bill"], pd.DataFrame([totals_row])], ignore_index=True)

    # Display the bill with totals
    st.write("### Bill:-")
    st.dataframe(bill_with_totals)