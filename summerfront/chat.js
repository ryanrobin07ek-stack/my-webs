// api/chat.js
//
// Serverless endpoint for the chat widget. Deploy as a Vercel function
// (should be an easy port to Netlify/Cloudflare Workers too). Whole reason
// this lives on the server and not in the front-end JS is so the OpenRouter
// key never has to touch the browser.
//
// Set OPENROUTER_API_KEY in your host's env var dashboard - don't hardcode
// it here and definitely don't commit it.

// Free models we try in order. If one's rate-limited or down we just fall
// through to the next one instead of failing the whole request.
const FALLBACK_MODELS = [
  "openrouter/free",
  "meta-llama/llama-3.3-70b-instruct:free",
  "openai/gpt-oss-120b:free",
  "qwen/qwen3-coder:free",
];

const SYSTEM_PROMPT = `You are the friendly virtual host for Summer Front, a restaurant with locations across the Kenyan coast (Mombasa area) and Nairobi. You help guests with: recommending dishes from the menu, explaining categories (Appetizers/Starters, Soups & Salads, Main Course, Sides, Desserts, Platters, Kids Menu, Dietary, Beverages, Breakfast, Lunch Specials, Daily Specials), answering general questions about hours, locations and finding the nearest branch, and helping with reservations or catering questions. Locations generally open between 6:30-8:00 AM and close between 9:00-11:00 PM, with a few 24-hour branches. Exact hours and phone numbers vary per branch - for a specific branch, politely direct the guest to the Locations page on this site so they get the current, exact details rather than guessing. Keep replies warm, concise (2-4 sentences unless asked for detail), and helpful. If you don't know something specific (like a live table availability), say so honestly and suggest calling the branch or using the site's booking form.`;

module.exports = async (req, res) => {
  if (req.method !== "POST") {
    return res.status(405).json({ error: "POST only" });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    // missing env var - nothing we can do here except tell the client
    return res.status(500).json({ error: "server not configured" });
  }

  const incomingMessages = Array.isArray(req.body?.messages) ? req.body.messages : [];

  // Try each model until one of them actually gives us a reply back.
  for (const model of FALLBACK_MODELS) {
    let response;
    try {
      response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
          "HTTP-Referer": req.headers.origin || "https://summerfront.example",
          "X-Title": "Summer Front",
        },
        body: JSON.stringify({
          model,
          messages: [{ role: "system", content: SYSTEM_PROMPT }, ...incomingMessages],
          temperature: 0.7,
          max_tokens: 400,
        }),
      });
    } catch (err) {
      // network hiccup, dead endpoint, whatever - just move on to the next model
      continue;
    }

    if (!response.ok) continue;

    const data = await response.json();
    const reply = data?.choices?.[0]?.message?.content;
    if (!reply) continue; // some free models occasionally return an empty completion

    return res.status(200).json({ reply: reply.trim() });
  }

  // every model in the list failed - nothing more we can do
  res.status(502).json({ error: "all models failed" });
};
