import axios from 'axios'
import type {
  Activity,
  AgentStatus,
  CollectionRun,
  ContentIdeaCategory,
  Country,
  CustomWatchResult,
  DashboardSummary,
  GiftCardType,
  Platform,
  PriceBoardCell,
  PriceQuote,
  SocialPost,
} from '../types'

export const api = axios.create({ baseURL: '/api' })

export const fetchCountries = () => api.get<Country[]>('/countries').then((r) => r.data)

export const fetchPlatforms = (countryCode?: string) =>
  api.get<Platform[]>('/platforms', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchGiftCardTypes = () => api.get<GiftCardType[]>('/gift-card-types').then((r) => r.data)

export const fetchPriceBoard = (countryCode?: string) =>
  api.get<PriceBoardCell[]>('/prices/board', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchPriceHistory = (platformId: number, giftCardTypeId: number, days = 30) =>
  api
    .get<PriceQuote[]>('/prices/history', {
      params: { platform_id: platformId, gift_card_type_id: giftCardTypeId, days },
    })
    .then((r) => r.data)

export const fetchActivities = (countryCode?: string, limit = 50) =>
  api.get<Activity[]>('/activities', { params: { country_code: countryCode, limit } }).then((r) => r.data)

export const fetchSocialPosts = (countryCode?: string, limit = 50) =>
  api.get<SocialPost[]>('/social', { params: { country_code: countryCode, limit } }).then((r) => r.data)

export const fetchDashboardSummary = (countryCode?: string) =>
  api.get<DashboardSummary>('/dashboard/summary', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchAgentStatus = () => api.get<AgentStatus>('/dashboard/agent-status').then((r) => r.data)

export const fetchIdeas = () => api.get<ContentIdeaCategory[]>('/ideas').then((r) => r.data)

export const fetchRuns = (limit = 20) => api.get<CollectionRun[]>('/collect/runs', { params: { limit } }).then((r) => r.data)

export const triggerCollection = (scope: 'price' | 'activity' | 'social' | 'all', countryCode?: string) =>
  api
    .post<CollectionRun[]>('/collect/run', null, { params: { scope, country_code: countryCode } })
    .then((r) => r.data)

export const runCustomWatch = (query: string, label: string) =>
  api.post<CustomWatchResult[]>('/collect/custom', { query, label }).then((r) => r.data)
