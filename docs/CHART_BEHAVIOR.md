# Chart Behavior - DB Report Chat App

## 📊 Chart Types & Behavior

The DB Report Chat App supports multiple chart types with both static and interactive display options.

### Supported Chart Types

| Chart Type | Keywords | Description | Use Case |
|------------|----------|-------------|----------|
| **Bar** | "bar chart", "bar diagram" | Vertical/horizontal bars | Comparisons between categories |
| **Line** | "line chart", "line diagram" | Connected data points | Trends over time |
| **Pie** | "pie chart", "pie diagram" | Circular segments | Proportion breakdowns |
| **Scatter** | "scatter plot", "scatter chart" | Data point distribution | Relationships between variables |
| **Stack** | "stack chart", "stacked chart" | Stacked bars | Layered comparisons |

## 🎯 Display Modes

### Static Images (Default)
- **Format**: PNG images generated server-side
- **Advantages**: Cross-platform compatibility, no JavaScript dependencies
- **Generation**: Matplotlib on server, converted to base64 or file

### Interactive Charts (Optional)
- **Format**: Chart.js canvas elements
- **Advantages**: Hover tooltips, zoom, responsive design
- **Toggle**: Individual chart mode switching

## 🔧 Technical Implementation

### Static Chart Flow
```
User Request → SQL Query → DataFrame → Matplotlib → PNG Image → Frontend Display
```

### Interactive Chart Flow
```
User Request → SQL Query → DataFrame → JSON Data → Chart.js → Canvas Element
```

### Code Locations
- **Static Charts**: `utils/response_formatter.py` → `generate_visualization()`
- **Interactive Charts**: `templates/index.html` → `createInteractiveChart()`
- **Toggle Logic**: `templates/index.html` → `toggleChartMode()`

## 🎨 Chart Configuration

### Static Chart Settings
```python
# In utils/response_formatter.py
plt.figure(figsize=(10, 5))  # Chart size
plt.style.use('seaborn-v0_8')  # Style
plt.savefig(buf, format='png', dpi=120)  # Quality
```

### Interactive Chart Settings
```javascript
// In templates/index.html
const chartConfig = {
    options: {
        responsive: true,
        plugins: {
            title: { display: true, text: 'Chart Title' }
        }
    }
};
```

## 📈 Performance Comparison

| Feature | Static Images | Interactive Charts |
|---------|---------------|-------------------|
| **Load Time** | Fast | Slightly slower |
| **Memory Usage** | Low | Higher |
| **Browser Compatibility** | Excellent | Good |
| **Data Exploration** | Limited | Excellent |
| **File Size** | Small | Larger (Chart.js library) |
| **Offline Support** | Yes | Yes |

## 🚀 Usage Guidelines

### When to Use Static Charts
- ✅ Production environments
- ✅ Limited bandwidth
- ✅ Simple data visualization
- ✅ Consistent appearance requirements
- ✅ Mobile applications

### When to Use Interactive Charts
- ✅ Data exploration sessions
- ✅ Complex datasets
- ✅ User interaction requirements
- ✅ Development/testing environments
- ✅ Desktop applications

## 🔄 Mode Switching

### Toggle Button
Each chart displays a contextual toggle button:
- **Static Chart**: `📈 Switch to Interactive` (blue)
- **Interactive Chart**: `📷 Switch to Static` (green)

### Switching Process
1. **Click the button** next to any chart
2. **Chart transforms immediately** (no page reload needed)
3. **Individual control** - each chart can be different
4. **Persistent preference** - choice remembered for future charts

## ⚙️ Configuration

### Default Mode
```javascript
let useInteractiveCharts = localStorage.getItem('useInteractiveCharts') === 'true'; // Default: Static charts
```

### Persistent Settings
The chart mode preference is automatically saved to localStorage and persists across:
- ✅ Page reloads
- ✅ Browser sessions
- ✅ Browser restarts
- ✅ Tab closures and reopening

## 🐛 Troubleshooting

### Static Charts Not Showing
- Check if `static/generated/` directory exists
- Verify file permissions
- Check browser console for image loading errors

### Interactive Charts Not Working
- Ensure Chart.js is loaded (check network tab)
- Verify data format in browser console
- Check for JavaScript errors

### Toggle Button Not Working
- Refresh the page
- Check browser console for errors
- Verify button ID matches JavaScript

## 📊 Chart Generation Examples

### Bar Chart
```
"Create a bar chart of sales by month"
"Show me a bar diagram of employee count by department"
```

### Line Chart
```
"Generate a line chart of revenue over time"
"Show me a line diagram of website traffic"
```

### Pie Chart
```
"Create a pie chart of sales by category"
"Show me a pie diagram of market share"
```

### Scatter Plot
```
"Generate a scatter plot of price vs quality"
"Show me a scatter chart of age vs salary"
```

### Stack Chart
```
"Sales by date stack chart"
"Create a stacked bar chart of revenue by region"
```

## 🔧 Advanced Features

### Data Preview
- Interactive charts show data preview in development mode
- Hover tooltips display exact values
- Responsive design adapts to container size

### Chart Customization
- Automatic color schemes
- Responsive sizing
- Professional styling
- Export capabilities

### Error Handling
- Graceful fallback to table format
- Error logging for debugging
- User-friendly error messages

## 📚 Resources

- **Matplotlib Documentation**: https://matplotlib.org/
- **Chart.js Documentation**: https://www.chartjs.org/
- **Flask Static Files**: https://flask.palletsprojects.com/en/2.3.x/quickstart/#static-files

---

**Note**: Static images are recommended for production use. Interactive charts are provided as an enhancement for data exploration scenarios. 