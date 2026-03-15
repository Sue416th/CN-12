import axios from "axios";

const API_BASE_URL = "/cultural";

export interface ChatMessage {
  role: "user" | "ai";
  content: string;
  images?: string[];
}

export interface ChatResponse {
  answer: string;
  images: string[];
  keywords: string;
}

export async function sendChatMessage(message: string): Promise<ChatResponse> {
  const response = await axios.post<ChatResponse>(
    `${API_BASE_URL}/api/cultural/chat/images`,
    { message },
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );
  return response.data;
}
