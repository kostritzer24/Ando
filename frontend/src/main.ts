import { createPinia } from "pinia";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./app/router";
import { useAuthStore } from "./features/auth/stores/authStore";
import "./design/tokens.css";

const app = createApp(App);
app.use(createPinia());

// Se reconstruye la sesión (si hay cookie de refresco válida) antes de
// activar el router: así el guard de la primera navegación ya sabe quién
// es el usuario, en vez de mandarlo a /ingresar por una fracción de
// segundo mientras la restauración todavía está en curso.
const auth = useAuthStore();
await auth.restaurarSesion();

app.use(router);
app.mount("#app");
