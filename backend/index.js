import cors from "cors";
import express from "express";
import { ChatGPTUnofficialProxyAPI } from "chatgpt";

// Initialize express
const app = express();

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.post("/query", async (req, res) => {
    const { prompt, accessToken } = req.body;

    console.log(`[INFO] Prompt: ${prompt}`);

    const api = new ChatGPTUnofficialProxyAPI({
        accessToken: accessToken,
        apiReverseProxyUrl: "https://ai.fakeopen.com/api/conversation"
    });

    const response = await api.sendMessage(prompt).then((res) => res.text);

    console.log(response);

    return res.status(200).json({ message: response });
});

// Start server
app.listen(5000, () => {
    console.log("Server running on port 5000");
});
