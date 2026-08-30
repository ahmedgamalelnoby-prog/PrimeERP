import type { ReactNode } from "react";

import { AuthProvider } from "../../modules/identity";

interface AppProviderProps {
    children: ReactNode;
}

export default function AppProvider({
    children,
}: AppProviderProps) {

    return (

        <AuthProvider>

            {children}

        </AuthProvider>

    );

}