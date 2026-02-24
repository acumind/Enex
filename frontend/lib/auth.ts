/**
 * NextAuth v5 config — used only for Google OAuth redirect flow.
 * The backend owns all JWTs; NextAuth just captures the Google id_token.
 */
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          prompt: "consent",
          access_type: "offline",
          response_type: "code",
        },
      },
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // Capture the Google id_token on first sign-in
      if (account) {
        token.id_token = account.id_token;
        token.access_token = account.access_token;
      }
      return token;
    },
    async session({ session, token }) {
      // Expose Google tokens to the client for backend exchange
      (session as unknown as Record<string, unknown>).id_token = token.id_token;
      (session as unknown as Record<string, unknown>).access_token = token.access_token;
      return session;
    },
  },
  pages: {
    signIn: "/login",
  },
});
