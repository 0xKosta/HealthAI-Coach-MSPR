import { describe, expect, it } from 'vitest'
import { isNetworkFailure, OFFLINE_MESSAGE } from './apiStatusStore'

describe('apiStatusStore helpers', () => {
  it('expose un message offline utilisateur', () => {
    expect(OFFLINE_MESSAGE).toMatch(/indisponible/i)
  })

  it('détecte une erreur réseau sans réponse HTTP', () => {
    expect(isNetworkFailure({ code: 'ERR_NETWORK' })).toBe(true)
    expect(isNetworkFailure({ message: 'Network Error' })).toBe(true)
  })

  it('ignore une erreur API avec statut HTTP', () => {
    expect(isNetworkFailure({ response: { status: 502 } })).toBe(false)
  })
})
