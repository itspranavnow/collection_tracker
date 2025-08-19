# 🕉️ Ganesh Chavithi Chanda Tracker

A beautiful and user-friendly Streamlit web application for tracking Ganesh Chavithi Chanda Collections and Expenses in your colony. Built with modern UI design and festive colors to celebrate the spirit of Ganesh Chaturthi.

## ✨ Features

### 🧾 Chanda Collections Tab
- **Summary Cards**: Total collected, total due, paid donors count, due donors count
- **Search & Filter**: Search by donor name, filter by type (Civic, Basic, Intrinsic, Classic) and status (Paid/Due)
- **Interactive Charts**: Pie chart showing amount distribution by type, bar chart for paid vs due amounts
- **Download Data**: Export filtered collections as CSV
- **Beautiful UI**: Colorful badges and status indicators

### 💰 Expenses Tab
- **Expense Summary**: Total expenses displayed in an attractive card
- **Expense Details**: Complete list of all expenses with costs
- **Visual Charts**: Bar chart showing expense breakdown
- **Download Data**: Export expenses as CSV

### 🎨 UI/UX Features
- **Festive Design**: Warm colors (saffron, red, yellow, green) celebrating Ganesh Chaturthi
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Interactive Elements**: Hover effects, smooth transitions, and modern styling
- **Status Indicators**: Color-coded badges for paid (✅) and due (❌) status
- **Type Badges**: Beautiful gradient badges for different collection types

## 📁 File Structure

```
ganesh-chavithi-tracker/
│
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── collections.xlsx       # Collections data (Name, Amount, Type, Status)
├── expenses.xlsx          # Expenses data (Expense Name, Cost)
├── create_sample_data.py  # Script to generate sample data
└── README.md             # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Sample Data (Optional)

If you don't have your own Excel files, run this to create sample data:

```bash
python create_sample_data.py
```

### 3. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## 📊 Data Format

### Collections Excel File (`collections.xlsx`)
| Column | Description | Example |
|--------|-------------|---------|
| `Name` | Donor's name | "Ramesh Kumar" |
| `Amount` | Contribution amount | 1000 |
| `Type` | Category type | "Civic", "Basic", "Intrinsic", "Classic" |
| `Status` | Payment status | "Paid" or "Due" |

### Expenses Excel File (`expenses.xlsx`)
| Column | Description | Example |
|--------|-------------|---------|
| `Expense Name` | Name of the expense | "Ganesh Idol" |
| `Cost` | Cost amount | 5000 |

## 🌐 Deployment

### Deploy to Streamlit Community Cloud

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/yourusername/ganesh-chavithi-tracker.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set the main file path as `app.py`
   - Click "Deploy"

### Deploy to Heroku

1. Create a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

2. Deploy using Heroku CLI or GitHub integration

## 🛠️ Customization

### Changing Colors
Edit the CSS in `app.py` to customize the color scheme:

```css
.main-header {
    background: linear-gradient(90deg, #YOUR_COLOR1, #YOUR_COLOR2, #YOUR_COLOR3);
}
```

### Adding New Features
The app is modular and easy to extend. You can:
- Add new tabs for different data types
- Create additional charts and visualizations
- Implement data entry forms
- Add user authentication

## 📱 Mobile Responsive

The app is fully responsive and works great on:
- 📱 Mobile phones
- 📱 Tablets
- 💻 Desktop computers
- 🖥️ Large screens

## 🎯 Key Features Summary

- ✅ **Real-time Data Loading**: Automatically loads fresh data from Excel files
- ✅ **Search & Filter**: Find donors quickly with case-insensitive search
- ✅ **Visual Analytics**: Beautiful charts and graphs
- ✅ **Export Functionality**: Download data as CSV files
- ✅ **Festive Design**: Ganesh Chaturthi themed colors and styling
- ✅ **Mobile Friendly**: Responsive design for all devices
- ✅ **Easy Deployment**: Ready for Streamlit Community Cloud

## 🤝 Contributing

Feel free to contribute to this project by:
- Reporting bugs
- Suggesting new features
- Improving the UI/UX
- Adding new functionality

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with ❤️ for Ganesh Chaturthi celebrations
- Powered by Streamlit for beautiful web applications
- Uses Plotly for interactive visualizations
- Pandas for efficient data handling

---

**🕉️ Ganpati Bappa Morya! 🕉️**

*May Lord Ganesh bless your celebrations and bring prosperity to all!*
