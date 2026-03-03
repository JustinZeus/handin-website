import { createRouter, createWebHistory } from "vue-router";
import PageView from "@/views/PageView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/:slug",
      name: "page",
      component: PageView,
    },
  ],
});

export default router;
