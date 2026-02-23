import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  ActivityIndicator,
} from "react-native";
import { useState, useRef } from "react";
import { Ionicons } from "@expo/vector-icons";
import { API_BASE_URL } from "../../src/api/client";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatScreen() {
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [starting, setStarting] = useState(false);
  const listRef = useRef<FlatList>(null);

  const startSession = async () => {
    setStarting(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/chat/session`, {
        method: "POST",
      });
      const data = await res.json();
      setSessionToken(data.session_token);
      setMessages([]);
    } finally {
      setStarting(false);
    }
  };

  const send = async () => {
    if (!input.trim() || !sessionToken || loading) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/chat/session/${sessionToken}/message`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text }),
        }
      );

      if (!response.body) return;
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const raw = decoder.decode(value, { stream: true });
        for (const line of raw.split("\n")) {
          if (line.startsWith("data: ")) accumulated += line.slice(6);
          else if (line.trim()) accumulated += line;
        }
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: accumulated };
          return updated;
        });
      }
    } finally {
      setLoading(false);
      setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      keyboardVerticalOffset={90}
    >
      {!sessionToken ? (
        <View style={styles.startScreen}>
          <Ionicons name="chatbubbles-outline" size={64} color="#d1d5db" />
          <Text style={styles.startTitle}>AI FAQ Assistant</Text>
          <Text style={styles.startSubtitle}>
            Ask about pricing, availability, aftercare, and more
          </Text>
          <TouchableOpacity style={styles.startBtn} onPress={startSession} disabled={starting}>
            {starting ? (
              <ActivityIndicator color="#ffffff" />
            ) : (
              <Text style={styles.startBtnText}>Start Chat</Text>
            )}
          </TouchableOpacity>
        </View>
      ) : (
        <>
          <FlatList
            ref={listRef}
            data={messages}
            keyExtractor={(_, i) => String(i)}
            contentContainerStyle={styles.messageList}
            onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
            ListEmptyComponent={
              <Text style={styles.emptyChat}>
                Session active — ask anything!
              </Text>
            }
            renderItem={({ item: msg }) => (
              <View
                style={[
                  styles.bubble,
                  msg.role === "user" ? styles.userBubble : styles.aiBubble,
                ]}
              >
                <Text
                  style={[
                    styles.bubbleText,
                    msg.role === "user" ? styles.userText : styles.aiText,
                  ]}
                >
                  {msg.content}
                </Text>
              </View>
            )}
          />

          {loading && (
            <View style={styles.typingIndicator}>
              <ActivityIndicator size="small" color="#7c3aed" />
              <Text style={styles.typingText}>Thinking...</Text>
            </View>
          )}

          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={input}
              onChangeText={setInput}
              placeholder="Ask a question..."
              placeholderTextColor="#9ca3af"
              multiline
              maxLength={500}
              onSubmitEditing={send}
            />
            <TouchableOpacity
              style={[styles.sendBtn, (!input.trim() || loading) && styles.sendBtnDisabled]}
              onPress={send}
              disabled={!input.trim() || loading}
            >
              <Ionicons name="send" size={18} color="#ffffff" />
            </TouchableOpacity>
          </View>
        </>
      )}
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  startScreen: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: 32,
  },
  startTitle: { fontSize: 22, fontWeight: "700", color: "#111827", marginTop: 16 },
  startSubtitle: {
    fontSize: 14,
    color: "#6b7280",
    textAlign: "center",
    marginTop: 8,
    marginBottom: 28,
    lineHeight: 20,
  },
  startBtn: {
    backgroundColor: "#7c3aed",
    borderRadius: 14,
    paddingHorizontal: 32,
    paddingVertical: 14,
  },
  startBtnText: { color: "#ffffff", fontWeight: "700", fontSize: 16 },
  messageList: { padding: 16, paddingBottom: 8 },
  emptyChat: { textAlign: "center", color: "#9ca3af", fontSize: 13, marginTop: 24 },
  bubble: {
    maxWidth: "80%",
    borderRadius: 18,
    padding: 12,
    marginBottom: 8,
  },
  userBubble: {
    backgroundColor: "#7c3aed",
    alignSelf: "flex-end",
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    backgroundColor: "#ffffff",
    alignSelf: "flex-start",
    borderBottomLeftRadius: 4,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  bubbleText: { fontSize: 15, lineHeight: 22 },
  userText: { color: "#ffffff" },
  aiText: { color: "#111827" },
  typingIndicator: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 20,
    paddingBottom: 4,
    gap: 6,
  },
  typingText: { fontSize: 12, color: "#6b7280" },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 12,
    paddingBottom: 16,
    backgroundColor: "#ffffff",
    borderTopWidth: 1,
    borderTopColor: "#e5e7eb",
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: "#f3f4f6",
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 15,
    color: "#111827",
    maxHeight: 120,
  },
  sendBtn: {
    backgroundColor: "#7c3aed",
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: "center",
    justifyContent: "center",
  },
  sendBtnDisabled: { opacity: 0.4 },
});
