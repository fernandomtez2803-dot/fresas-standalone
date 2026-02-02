import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: 'Fresas Standalone',
    description: 'Control de fresas con código de barras',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="es">
            <body className="min-h-screen bg-slate-900">
                {children}
            </body>
        </html>
    )
}
