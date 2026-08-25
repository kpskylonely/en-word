import { createRouter, createWebHistory } from "vue-router";
import HomeView from "../views/HomeView.vue";
import StudyView from "../views/StudyView.vue";
import BrowseView from "../views/BrowseView.vue";
import FlashcardView from "../views/FlashcardView.vue";
import QuizView from "../views/QuizView.vue";
import SpellingView from "../views/SpellingView.vue";
import WrongBookView from "../views/WrongBookView.vue";
import SettingsView from "../views/SettingsView.vue";
import StatsView from "../views/StatsView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: HomeView },
    { path: "/study", name: "study", component: StudyView },
    { path: "/browse", name: "browse", component: BrowseView },
    { path: "/flashcard", name: "flashcard", component: FlashcardView },
    { path: "/quiz/:mode", name: "quiz", component: QuizView },
    { path: "/spelling", name: "spelling", component: SpellingView },
    { path: "/study/wrong", name: "study-wrong", component: WrongBookView, meta: { wrongScope: "book" } },
    { path: "/wrong", name: "wrong", component: WrongBookView, meta: { wrongScope: "all" } },
    { path: "/stats", name: "stats", component: StatsView },
    { path: "/settings", name: "settings", component: SettingsView },
  ],
});

export default router;
