# Facty: Kid-Friendly Fact Checker Chat UI

This project is a vibrant, playful, and accessible fact-checker chat app for children, built with Next.js and Tailwind CSS. It connects to a FastAPI backend at `/chat` for fact-checking using a Hugging Face model.

## Features

- Bright, modern, and kid-friendly design
- Responsive single-page layout
- Title, logo, and explanatory text
- Chatbox for interacting with Facty (the bot)
- Connects to FastAPI backend at `/chat`

## Getting Started

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Run the development server:**

   ```bash
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000) in your browser.

3. **Build for production:**

   ```bash
   npm run build
   npm start
   ```

## Deployment

Deploy easily for free on [Vercel](https://vercel.com/). This project is optimized for Vercel hosting.

## Customization

- Update the logo in `/public` as needed.
- Adjust theme colors in `tailwind.config.js` for your own vibrant palette.

## Backend

- The chatbox expects a FastAPI backend running at `/chat` (see backend folder for details).

---

*Made with ❤️ for curious kids!*
