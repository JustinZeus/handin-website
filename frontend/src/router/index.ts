import { createRouter, createWebHistory } from "vue-router";
import PageView from "@/views/PageView.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: () => {
        // Will be redirected to first page after pages load
        return "/";
      },
    },
    {
      path: "/:slug",
      name: "page",
      component: PageView,
    },
  ],
});

export default router;
