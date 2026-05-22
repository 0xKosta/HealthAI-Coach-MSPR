import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '@/views/DashboardView.vue'
import NutritionView from '@/views/NutritionView.vue'
import WorkoutView from '@/views/WorkoutView.vue'
import ExercisesView from '@/views/ExercisesView.vue'
import TrendsView from '@/views/TrendsView.vue'

const routes = [
  { path: '/',           name: 'Dashboard', component: DashboardView },
  { path: '/nutrition',  name: 'Nutrition', component: NutritionView },
  { path: '/workout',    name: 'Workout',   component: WorkoutView },
  { path: '/exercises',  name: 'Exercises', component: ExercisesView },
  { path: '/trends',     name: 'Trends',    component: TrendsView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 })
})
