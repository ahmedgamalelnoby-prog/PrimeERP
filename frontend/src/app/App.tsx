import AppProvider from "./providers/AppProvider";

import { AppRouter } from "./router";

export default function App() {

    return (

        <AppProvider>

            <AppRouter />

        </AppProvider>

    );

}