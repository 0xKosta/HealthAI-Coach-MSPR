import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import NutritionView from '@/views/NutritionView.vue'
import WorkoutView from '@/views/WorkoutView.vue'
import ExercisesView from '@/views/ExercisesView.vue'
import TrendsView from '@/views/TrendsView.vue'
import TrendsUsersView from '@/views/TrendsUsersView.vue'

const routes = [
  { path: '/', redirect: '/admin' },
  { path: '/admin',                          name: 'AdminUsers', component: TrendsUsersView },
  { path: '/admin/dashboard/:userId',        name: 'Dashboard',  component: DashboardView },
  { path: '/admin/dashboard/:userId/trends', name: 'Trends',     component: TrendsView },
  { path: '/admin/dashboard/:userId/nutrition', name: 'Nutrition', component: NutritionView },
  { path: '/admin/dashboard/:userId/workout',   name: 'Workout',   component: WorkoutView },
  { path: '/exercises',  name: 'Exercises', component: ExercisesView },
  { path: '/dashboard/:userId',         redirect: (to) => `/admin/dashboard/${to.params.userId}` },
  { path: '/dashboard/:userId/trends',  redirect: (to) => `/admin/dashboard/${to.params.userId}/trends` },
  { path: '/nutrition',                 redirect: '/admin' },
  { path: '/workout',                   redirect: '/admin' },
  { path: '/trends',                    redirect: '/admin' },
  { path: '/trends/:userId',            redirect: (to) => `/admin/dashboard/${to.params.userId}/trends` },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})
