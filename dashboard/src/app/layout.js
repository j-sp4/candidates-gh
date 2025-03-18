import './globals.css';

export const metadata = {
  title: 'GitHub Data Dashboard',
  description: 'Visualize GitHub repository and contributor data',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        {children}
      </body>
    </html>
  );
} 