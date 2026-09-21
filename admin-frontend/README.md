# Admin Frontend

The web-based operations dashboard for the Kalyan Simulator, built with Next.js 14, React 18, and Tailwind CSS.

## Features
- **Analytics Dashboard**: Visual charts and statistics using Recharts.
- **Operations Management**: Handle markets, configure game rates, publish game results, and manage users.
- **Type-Safe API Client**: Fully typed data fetching using React Query and OpenAPI-generated TypeScript definitions connected to the FastAPI backend.

## Setup Instructions

1. Ensure the backend is running locally on `http://localhost:8000`.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## Available Scripts

- `npm run dev`: Starts the local development server on port 3000.
- `npm run build`: Builds the Next.js application for production.
- `npm run start`: Starts the production server.
- `npm run lint`: Runs ESLint for code quality checks.
- `npm run gen:types`: Generates `lib/api/schema.d.ts` from the running backend's OpenAPI schema. **Requires the FastAPI server to be running on port 8000.**
