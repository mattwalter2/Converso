//
//  testview1.swift
//  Converso
//
//  Created by Matthew Walter on 10/20/23.
//

import SwiftUI

struct testview1: View {
    var message: String?
    var body: some View {
        Text(message ?? "Hello")
       
    }
}

#Preview {
    testview1(message: nil)
}
