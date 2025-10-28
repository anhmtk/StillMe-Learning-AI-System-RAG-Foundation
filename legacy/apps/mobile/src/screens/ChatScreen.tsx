// StillMe Mobile - Chat Screen
import React, { useState, useEffect, useRef } from 'react';
import { View, StyleSheet, FlatList, KeyboardAvoidingView, Platform } from 'react-native';
import { Text, TextInput, Button, Card, Avatar, IconButton } from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../store/store';
import { addMessage, setTyping, markAsRead } from '../store/slices/chatSlice';
import { WebSocketService } from '../services/websocket';
import { theme } from '../theme/theme';

interface ChatMessage {
  id: string;
  content: string;
  timestamp: number;
  isUser: boolean;
  status: 'sending' | 'sent' | 'delivered' | 'failed';
}

const ChatScreen: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { messages, isTyping, unreadCount } = useSelector((state: RootState) => state.chat);
  const { connectionStatus } = useSelector((state: RootState) => state.app);
  
  const [inputText, setInputText] = useState('');
  const [wsService] = useState(new WebSocketService());
  const flatListRef = useRef<FlatList>(null);

  useEffect(() => {
    initializeWebSocket();
    dispatch(markAsRead());
  }, []);

  useEffect(() => {
    // Scroll to bottom when new message arrives
    if (messages.length > 0) {
      setTimeout(() => {
        flatListRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages.length]);

  const initializeWebSocket = async () => {
    try {
      await wsService.initialize();
      
      wsService.on('connected', () => {
        console.log('WebSocket connected');
      });

      wsService.on('disconnected', () => {
        console.log('WebSocket disconnected');
      });

      wsService.on('message', (message) => {
        handleIncomingMessage(message);
      });

      wsService.on('command_response', (response) => {
        handleCommandResponse(response);
      });

    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
    }
  };

  const handleIncomingMessage = (message: any) => {
    if (message.type === 'notification') {
      const chatMessage: ChatMessage = {
        id: `msg_${Date.now()}`,
        content: message.data?.body || message.message || 'New notification',
        timestamp: Date.now(),
        isUser: false,
        status: 'delivered',
      };
      dispatch(addMessage(chatMessage));
    }
  };

  const handleCommandResponse = (response: any) => {
    const chatMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      content: response.data?.result || response.message || 'Command executed',
      timestamp: Date.now(),
      isUser: false,
      status: 'delivered',
    };
    dispatch(addMessage(chatMessage));
  };

  const sendMessage = async () => {
    if (!inputText.trim() || !wsService.isConnected) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      content: inputText.trim(),
      timestamp: Date.now(),
      isUser: true,
      status: 'sending',
    };

    dispatch(addMessage(userMessage));
    dispatch(setTyping(true));

    try {
      // Send command to StillMe Core
      const success = wsService.sendCommand('chat', {
        message: inputText.trim(),
        context: {
          platform: 'mobile',
          timestamp: Date.now(),
        },
      });

      if (success) {
        // Update message status
        setTimeout(() => {
          dispatch(addMessage({
            ...userMessage,
            status: 'sent',
          }));
        }, 100);
      } else {
        // Update message status to failed
        dispatch(addMessage({
          ...userMessage,
          status: 'failed',
        }));
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      dispatch(addMessage({
        ...userMessage,
        status: 'failed',
      }));
    } finally {
      setInputText('');
      dispatch(setTyping(false));
    }
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => (
    <View style={[
      styles.messageContainer,
      item.isUser ? styles.userMessage : styles.botMessage
    ]}>
      <Avatar.Icon
        size={32}
        icon={item.isUser ? 'account' : 'robot'}
        style={[
          styles.avatar,
          item.isUser ? styles.userAvatar : styles.botAvatar
        ]}
      />
      <Card style={[
        styles.messageCard,
        item.isUser ? styles.userMessageCard : styles.botMessageCard
      ]}>
        <Card.Content>
          <Text style={styles.messageText}>{item.content}</Text>
          <Text style={styles.timestamp}>
            {new Date(item.timestamp).toLocaleTimeString()}
          </Text>
        </Card.Content>
      </Card>
    </View>
  );

  const renderTypingIndicator = () => {
    if (!isTyping) return null;
    
    return (
      <View style={[styles.messageContainer, styles.botMessage]}>
        <Avatar.Icon
          size={32}
          icon="robot"
          style={[styles.avatar, styles.botAvatar]}
        />
        <Card style={[styles.messageCard, styles.botMessageCard]}>
          <Card.Content>
            <Text style={styles.typingText}>StillMe is typing...</Text>
          </Card.Content>
        </Card>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView 
      style={styles.container} 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>StillMe AI</Text>
        <View style={styles.connectionStatus}>
          <View style={[
            styles.statusDot,
            { backgroundColor: connectionStatus === 'connected' ? '#4CAF50' : '#F44336' }
          ]} />
          <Text style={styles.statusText}>
            {connectionStatus === 'connected' ? 'Connected' : 'Disconnected'}
          </Text>
        </View>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        renderItem={renderMessage}
        keyExtractor={(item) => item.id}
        style={styles.messagesList}
        contentContainerStyle={styles.messagesContent}
        ListFooterComponent={renderTypingIndicator}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      <View style={styles.inputContainer}>
        <TextInput
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type your message..."
          mode="outlined"
          style={styles.textInput}
          multiline
          maxLength={1000}
          disabled={!wsService.isConnected}
        />
        <IconButton
          icon="send"
          mode="contained"
          onPress={sendMessage}
          disabled={!inputText.trim() || !wsService.isConnected}
          style={styles.sendButton}
        />
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: theme.colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: theme.colors.outline,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: theme.colors.primary,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 8,
  },
  statusText: {
    fontSize: 12,
    color: theme.colors.onSurfaceVariant,
  },
  messagesList: {
    flex: 1,
  },
  messagesContent: {
    padding: 16,
  },
  messageContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    alignItems: 'flex-end',
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  botMessage: {
    justifyContent: 'flex-start',
  },
  avatar: {
    marginHorizontal: 8,
  },
  userAvatar: {
    backgroundColor: theme.colors.primary,
  },
  botAvatar: {
    backgroundColor: theme.colors.secondary,
  },
  messageCard: {
    maxWidth: '80%',
  },
  userMessageCard: {
    backgroundColor: theme.colors.primary,
  },
  botMessageCard: {
    backgroundColor: theme.colors.surface,
  },
  messageText: {
    color: theme.colors.onSurface,
    fontSize: 16,
  },
  timestamp: {
    fontSize: 12,
    color: theme.colors.onSurfaceVariant,
    marginTop: 4,
  },
  typingText: {
    color: theme.colors.onSurfaceVariant,
    fontStyle: 'italic',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    backgroundColor: theme.colors.surface,
    borderTopWidth: 1,
    borderTopColor: theme.colors.outline,
    alignItems: 'flex-end',
  },
  textInput: {
    flex: 1,
    marginRight: 8,
    maxHeight: 100,
  },
  sendButton: {
    margin: 0,
  },
});

export default ChatScreen;
