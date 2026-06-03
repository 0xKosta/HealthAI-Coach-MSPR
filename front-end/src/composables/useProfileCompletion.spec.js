import { describe, expect, it } from 'vitest'
import {
  blocksAiFeatures,
  getProfileEditPath,
  isProfileIncomplete,
} from './useProfileCompletion'

describe('useProfileCompletion', () => {
  it('détecte un profil incomplet sans objectif', () => {
    expect(isProfileIncomplete({ age: 30, weight_kg: 70, height_cm: 175 })).toBe(true)
  })

  it('considère un profil complet comme prêt pour l’IA', () => {
    const user = {
      age: 30,
      weight_kg: 70,
      height_cm: 175,
      goal: 'weight_loss',
    }
    expect(isProfileIncomplete(user)).toBe(false)
    expect(blocksAiFeatures(user)).toBe(false)
  })

  it('bloque l’IA si l’âge est hors limites', () => {
    const user = {
      age: 15,
      weight_kg: 70,
      height_cm: 175,
      goal: 'weight_loss',
    }
    expect(blocksAiFeatures(user)).toBe(true)
  })

  it('construit le chemin d’édition admin', () => {
    expect(getProfileEditPath(42, { admin: true })).toBe('/admin/dashboard/42/profile')
  })
})
