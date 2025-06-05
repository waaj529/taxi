import pandas as pd
from core.database import get_db_connection
from datetime import datetime, timedelta

def km_per_driver(company_id: int, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """
    Calculates total kilometers driven per driver within a given period for a specific company.

    Args:
        company_id: The ID of the company.
        start_date: The start date of the period.
        end_date: The end date of the period.

    Returns:
        A Pandas DataFrame with columns ['driver', 'km']
    """
    conn = get_db_connection()
    # cursor = conn.cursor() # Not strictly needed if using pd.read_sql_query directly with params

    # Ensure dates are in YYYY-MM-DD string format for the SQL query
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    query = """
        SELECT 
            d.name AS driver_name,
            SUM(r.gefahrene_kilometer) AS total_km
        FROM rides r
        JOIN drivers d ON r.driver_id = d.id
        WHERE r.company_id = :company_id 
          AND DATE(r.pickup_time) BETWEEN :start_date AND :end_date
          AND r.gefahrene_kilometer IS NOT NULL
        GROUP BY d.name
        ORDER BY total_km DESC
    """
    
    params = {
        "company_id": company_id,
        "start_date": start_date_str,
        "end_date": end_date_str
    }

    try:
        df = pd.read_sql_query(query, conn, params=params)
    except Exception as e:
        print(f"Error executing SQL query in km_per_driver: {e}")
        # Return an empty DataFrame or re-raise, depending on desired error handling
        df = pd.DataFrame(columns=['driver_name', 'total_km']) 
    finally:
        if conn:
            conn.close()
    
    # Rename columns to match the expected output for the chart widget
    df.rename(columns={'driver_name': 'driver', 'total_km': 'km'}, inplace=True)
    
    return df

def example_placeholder_function_for_other_charts():
    # This is a placeholder for other analysis functions you might add
    # e.g., profit_per_vehicle, work_hours_vs_paid, etc.
    data = {'category': ['A', 'B', 'C'], 'value': [10, 20, 15]}
    df = pd.DataFrame(data)
    return df

# Example usage (for testing purposes, can be removed later)
if __name__ == '__main__':
    # This part would require the database to be initialized and have some data
    # Also, ensure your project structure allows direct execution for testing
    # from database import initialize_database
    # initialize_database() # Make sure this is safe to call or mock DB interactions

    print("Testing km_per_driver function...")
    # Create dummy dates for testing
    today = datetime.now()
    dummy_start_date = today - timedelta(days=30)
    dummy_end_date = today
    
    # Test with a placeholder company_id. Replace with a valid one from your DB for real testing.
    test_company_id = 1 
    
    try:
        km_data = km_per_driver(test_company_id, dummy_start_date, dummy_end_date)
        if not km_data.empty:
            print("Kilometers per driver:")
            print(km_data)
        else:
            print("No kilometer data returned. This might be normal if there's no data for the period/company.")
    except Exception as e:
        print(f"Error during km_per_driver test: {e}")

    print("\nTesting example_placeholder_function_for_other_charts:")
    placeholder_data = example_placeholder_function_for_other_charts()
    print(placeholder_data) 