import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { BookOpen, Send } from "lucide-react";
import cultureHero from "@/assets/culture-hero.jpg";
import dest1 from "@/assets/destination-1.jpg";
import dest2 from "@/assets/destination-2.jpg";
import dest3 from "@/assets/destination-3.jpg";
import { sendChatMessage, type ChatMessage } from "@/lib/cultural";

const AI_WELCOME =
  "Hello! I'm your cultural guide assistant. I can introduce the history and culture of famous attractions like West Lake, Lingyin Temple, and Leifeng Pagoda. What would you like to know?";

const articles = [
  { title: "Bai Tie-Dye Craft", desc: "A handcrafted art passed down for centuries, where every piece is one of a kind. Tie-dye is among China's oldest textile heritage traditions.", category: "Intangible Heritage", image: dest1 },
  { title: "Dali Three-Course Tea", desc: "Bitter first, sweet second, and lingering aftertaste - a ritual that reflects Bai hospitality and timeless life wisdom.", category: "Food Culture", image: dest2 },
  { title: "Naxi Dongba Culture", desc: "Home to the world's only living pictographic script, this cultural treasure carries centuries of memory and identity.", category: "Ethnic Culture", image: dest3 },
];

const Culture = () => {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "ai", content: AI_WELCOME, images: [] },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    const content = input.trim();
    if (!content || isLoading) return;

    setInput("");
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: "user", content, images: [] }]);

    try {
      const response = await sendChatMessage(content);
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: response.answer,
          images: response.images || [],
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          content: "Sorry, an error occurred. Please try again later.",
          images: [],
        },
      ]);
    }

    setIsLoading(false);
  };

  const openImage = (imgUrl: string) => {
    window.open(imgUrl, "_blank");
  };

  return (
    <div>
      {/* Hero */}
      <div className="relative h-72 overflow-hidden">
        <img src={cultureHero} alt="Culture" className="w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/40 to-transparent" />
        <div className="absolute inset-0 flex items-center">
          <div className="container max-w-6xl mx-auto px-6">
            <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }}>
              <h1 className="text-3xl font-display font-bold">Cultural Insights</h1>
              <p className="text-muted-foreground mt-2">Discover stories, traditions, and history behind every destination.</p>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="container max-w-6xl mx-auto px-6 py-10">
        {/* Chat Assistant Area */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="-mt-1 relative z-10 mb-10"
        >
          <div className="rounded-2xl bg-card border border-border/50 shadow-lg overflow-hidden min-h-[450px] flex flex-col w-full mx-auto">
            {/* 对话内容区 */}
            <div className="flex-1 p-6 pb-4 overflow-y-auto max-h-[500px]">
              {messages.map((msg, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 items-start mb-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                >
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-primary-foreground text-sm font-medium ${
                      msg.role === "user" ? "bg-gradient-to-br from-indigo-500 to-purple-600" : "bg-primary"
                    }`}
                  >
                    {msg.role === "user" ? "U" : "AI"}
                  </div>
                  <div
                    className={`rounded-xl px-4 py-3 max-w-[85%] shadow-sm ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-indigo-500 to-purple-600 text-white"
                        : "bg-muted/80 text-foreground"
                    }`}
                  >
                    <p className="text-base leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    {msg.images && msg.images.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {msg.images.map((img, imgIndex) => (
                          <img
                            key={imgIndex}
                            src={img}
                            alt={`Related image ${imgIndex + 1}`}
                            className="w-32 h-20 object-cover rounded-lg cursor-pointer hover:scale-105 transition-transform"
                            onClick={() => openImage(img)}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
              {isLoading && (
                <div className="flex gap-3 items-start">
                  <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center flex-shrink-0 text-primary-foreground text-sm font-medium">
                    AI
                  </div>
                  <div className="rounded-xl rounded-tl-sm bg-muted/80 px-4 py-3 shadow-sm">
                    <p className="text-base text-foreground">Thinking...</p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            {/* 输入区 */}
            <div className="p-4 pt-0 flex gap-3 items-center border-t border-border/50 bg-muted/30">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !isLoading && handleSend()}
                placeholder="Ask about any cultural attraction..."
                disabled={isLoading}
                className="flex-1 rounded-xl border border-input bg-background px-4 py-3 text-base placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 transition-shadow disabled:opacity-50"
              />
              <button
                type="button"
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-base font-medium text-primary-foreground shadow-sm hover:bg-primary/90 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </div>
          </div>
        </motion.div>

        {/* Articles */}
        <div className="flex items-center gap-2 mb-6">
          <BookOpen className="w-5 h-5 text-primary" />
          <h2 className="text-2xl font-display font-semibold">Local Culture</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {articles.map((article, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              whileHover={{ y: -4 }}
              className="rounded-xl bg-card border border-border/50 overflow-hidden shadow-sm hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="relative h-48 overflow-hidden">
                <img src={article.image} alt={article.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                <span className="absolute top-3 left-3 text-xs px-3 py-1 rounded-full bg-primary/90 text-primary-foreground font-medium">
                  {article.category}
                </span>
              </div>
              <div className="p-5">
                <h3 className="font-display font-semibold text-lg">{article.title}</h3>
                <p className="text-sm text-muted-foreground mt-2 line-clamp-2">{article.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Culture;
