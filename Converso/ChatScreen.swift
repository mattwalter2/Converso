import SwiftUI
import Alamofire

struct Message {
    let sender: String
    let message: String
}

struct ChatScreen: View {
    @State private var messages: [Message] = [
        Message(sender: "Chatbot", message: "Hello! How can I help you?"),
        Message(sender: "User", message: "I'd like to practice some SwiftUI!"),
        Message(sender: "Chatbot", message: "Sure! Let's get started."),
        Message(sender: "User", message: "Thanks!")
    ]
    @State private var currentMessage = ""
    
    var body: some View {
        VStack {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 10) {
                    ForEach(messages, id: \.message) { message in
                        MessageRow(message: message)
                    }
                }
            }.padding()
            Spacer()
            HStack {
                TextField("Enter a message here", text: $currentMessage)
                            .padding(10)
                            .background(
                                Capsule()
                                    .strokeBorder(Color.blue, lineWidth: 1)
                            )
                            .frame(height: 50)  // This ensures the capsule shape is horizontal
                            .padding(.horizontal, 5)
                Button(action: {
                    messages.append(Message(sender: "User", message: currentMessage))
                    // Handle button press here
                    print("Button pressed!")
                }) {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(Color.blue)
                        .overlay(
                                    Image(systemName: "arrow.right") // Using a system image for send
                                        .foregroundColor(.white) // Make the image white (or any other color)
                                )
                         // For example, fill with blue color
                        .frame(width: 50, height: 50)  // Specify the size of the rectangle
                }

            }
            
        }

    }
}

struct MessageRow: View {
    var message: Message
    
    var body: some View {
        HStack {
            if message.sender == "Chatbot" {
                MessageBubble(text: message.message, color: Color.gray)
                Spacer() // Push the message to the left if it's from Chatbot
            } else {
                Spacer() // Push the message to the right if it's from User
                MessageBubble(text: message.message, color: Color.orange)
            }
        }
    }
}

struct MessageBubble: View {
    var text: String
    var color: Color
    
    var body: some View {
        Text(text)
            .padding(10)
            .background(RoundedRectangle(cornerRadius: 15).fill(color))
    }
}

struct ChatScreen_Previews: PreviewProvider {
    static var previews: some View {
        ChatScreen()
    }
}

