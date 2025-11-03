# Tempora Frontend# React + Vite



React + Vite frontend for the Tempora intelligent calendar system.This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.



## SetupCurrently, two official plugins are available:



```powershell- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh

npm install- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

npm run dev

```## React Compiler



Access at: http://localhost:5173The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).



## Tech Stack## Expanding the ESLint configuration



- React 18+ with hooksIf you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

- FullCalendar for interactive calendar
- Axios for API calls
- Vite for fast development

## Main Components

- `Calendar.jsx` - Main calendar component (1,004 lines)
- `FormField.jsx` - Reusable form input
- `DurationInput.jsx` - Duration selector

## Configuration

API endpoint is configured in `Calendar.jsx`:
```javascript
const API_BASE_URL = "http://localhost:5000";
```

## Documentation

See [../README.md](../README.md) for complete project documentation.
