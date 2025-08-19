import pandas as pd
import numpy as np

# Create sample collections data
collections_data = {
    'Name': [
        'Ramesh Kumar', 'Priya Sharma', 'Amit Patel', 'Sunita Devi', 'Rajesh Singh',
        'Lakshmi Bai', 'Mohan Das', 'Kavita Reddy', 'Suresh Kumar', 'Anjali Gupta',
        'Vikram Malhotra', 'Meera Joshi', 'Prakash Tiwari', 'Rekha Verma', 'Dinesh Yadav',
        'Sita Ram', 'Harish Chandra', 'Uma Devi', 'Krishna Prasad', 'Lalita Kumari'
    ],
    'Amount': [
        1000, 500, 2000, 750, 1500, 300, 1200, 800, 2500, 600,
        1800, 400, 900, 1100, 700, 1600, 950, 1300, 1400, 850
    ],
    'Type': [
        'Civic', 'Basic', 'Intrinsic', 'Classic', 'Civic',
        'Basic', 'Intrinsic', 'Classic', 'Civic', 'Basic',
        'Intrinsic', 'Classic', 'Civic', 'Basic', 'Intrinsic',
        'Classic', 'Civic', 'Basic', 'Intrinsic', 'Classic'
    ],
    'Status': [
        'Paid', 'Paid', 'Due', 'Paid', 'Due',
        'Paid', 'Paid', 'Due', 'Paid', 'Paid',
        'Due', 'Paid', 'Due', 'Paid', 'Due',
        'Paid', 'Due', 'Paid', 'Paid', 'Due'
    ]
}

# Create sample expenses data
expenses_data = {
    'Expense Name': [
        'Ganesh Idol', 'Flowers & Decorations', 'Prasad Materials', 'Sound System',
        'Tent & Chairs', 'Lighting', 'Food & Refreshments', 'Transportation',
        'Priest Services', 'Cleaning Supplies', 'Miscellaneous'
    ],
    'Cost': [
        5000, 2500, 1800, 3000, 2000, 1500, 4000, 1200, 2000, 800, 1000
    ]
}

# Create DataFrames
collections_df = pd.DataFrame(collections_data)
expenses_df = pd.DataFrame(expenses_data)

# Save to Excel files
collections_df.to_excel('collections.xlsx', index=False)
expenses_df.to_excel('expenses.xlsx', index=False)

print("Sample Excel files created successfully!")
print(f"Collections: {len(collections_df)} records")
print(f"Expenses: {len(expenses_df)} records")
print("\nCollections Summary:")
print(f"Total Amount: ₹{collections_df['Amount'].sum():,.2f}")
print(f"Paid Amount: ₹{collections_df[collections_df['Status']=='Paid']['Amount'].sum():,.2f}")
print(f"Due Amount: ₹{collections_df[collections_df['Status']=='Due']['Amount'].sum():,.2f}")
print(f"\nExpenses Summary:")
print(f"Total Expenses: ₹{expenses_df['Cost'].sum():,.2f}")
