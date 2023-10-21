import SwiftUI

struct LanguageViewScreen: View {
    let languages = ["Spanish", "Chinese", "Italian", "Russian", "Portuguese", "Hindi"]
    let languagesHello = ["¡Hola!", "你好", "Ciao!", "привет!", "olá!", "नमस्ते!"]
    
    var body: some View {
        NavigationView {
            VStack {
                Text("Converso")
                    .font(.largeTitle)
                    .padding(.bottom, 20)
                
                
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 150))], spacing: 20) {
                  ForEach(Array(zip(languages, languagesHello)), id: \.0) { language, languageHello in
                    NavigationLink(destination: {
                      ChatScreen()
                    }) {
                      RoundedRectangle(cornerRadius: 15)
                        .fill(Color.orange)
                        .frame(width: 150, height: 150)
                        .overlay(
                          VStack(alignment: .leading) {
                            Text(language)
                              .font(.title2)
                              .fontWeight(.semibold)
                              .padding(.leading, 20)
                              .padding(.top, 20)

                            Text(languageHello)
                              .font(.title)
                              .padding(.leading, 20)
                          },
                          alignment: .topLeading
                        )
                      .padding() // Adds some space between the rectangles
                    }
                  }
                }

            }
        }

        .padding()
    }
}

struct LanguageViewScreen_Previews: PreviewProvider {
    static var previews: some View {
        LanguageViewScreen()
    }
}

