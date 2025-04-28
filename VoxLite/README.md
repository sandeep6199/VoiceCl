# VoxLite Flask App

This is a Flask web application for the VoxLite voice cloning technology service.

## Setup

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Project Structure

- `app.py` - Main Flask application
- `templates/` - HTML templates
- `static/` - Static files (CSS, JavaScript, images)
  - `css/` - Stylesheets
  - `js/` - JavaScript files
  - `images/` - Image assets

## Technology Used

- Flask
- HTML/CSS
- JavaScript

## Features

- Fully responsive design that works on mobile, tablet, and desktop
- Interactive UI with animations and transitions
- Modals for login, registration, and user dashboard
- Form validation for the contact form
- Interactive FAQ section
- Smooth scrolling navigation
- Password strength indicator
- Intersection Observer for scroll animations
- SVG illustrations with CSS animations

## File Structure

- `index.html` - The main HTML structure
- `styles.css` - All styling and animations
- `script.js` - JavaScript for interactions and functionality
- `hero-image.svg` - Custom SVG illustration for the hero section

## How to Use

1. Download or clone this repository
2. Open `index.html` in a web browser to view the website
3. No build process or dependencies required - it's pure HTML, CSS, and JavaScript

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Modifying the Site

### Colors

The color scheme can be easily modified by changing the CSS variables in the `:root` selector in `styles.css`:

```css
:root {
  --primary-color: #6366f1;
  --primary-hover: #4f46e5;
  --secondary-color: #10b981;
  /* other variables */
}
```

### Content

To update the content, simply edit the text within the HTML elements in `index.html`.

### Adding New Sections

To add new sections, follow the structure of existing sections in the HTML file and add corresponding styles in `styles.css`.

## Interactive Elements

- **Navigation**: The navigation menu transforms into a hamburger menu on mobile devices.
- **FAQ**: Click on questions to expand and view answers.
- **Modals**: Click on Login, Register, or the Profile button to open the corresponding modals.
- **Forms**: The Contact form includes validation.
- **Pricing Cards**: Hover effects show which plan is being considered.

## Credits

- Font Awesome for icons
- Inter font (loaded via Google Fonts)

## License

This project is available for use under the MIT License. 