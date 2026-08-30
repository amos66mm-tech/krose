export interface Country {
  id: number
  code: string
  name_zh: string
  name_en: string
  currency_code: string
  flag_emoji: string
}

export interface Platform {
  id: number
  country_id: number
  slug: string
  name: string
  website: string
  category: string
  logo_url: string
  twitter_handle: string
  facebook_handle: string
  instagram_handle: string
  telegram_handle: string
  trust_score: number
  notes: string
}

export interface GiftCardType {
  id: number
  slug: string
  name: string
  icon: string
}

export interface PriceBoardCell {
  platform_id: number
  platform_name: string
  gift_card_type_id: number
  gift_card_type_name: string
  gift_card_icon: string
  rate_percent: number
  currency: string
  is_new: boolean
  change_percent: number
  collected_at: string
  source_url: string
}

export interface PriceQuote {
  id: number
  platform_id: number
  gift_card_type_id: number
  direction: string
  rate_percent: number
  price_value: number
  currency: string
  unit_description: string
  source_url: string
  source_title: string
  is_new: boolean
  change_percent: number
  collected_at: string
}

export interface Activity {
  id: number
  platform_id: number
  activity_type: 'promotion' | 'announcement' | 'policy' | 'outage'
  title: string
  summary: string
  source_url: string
  published_at: string | null
  collected_at: string
}

export interface SocialPost {
  id: number
  platform_id: number
  network: string
  author: string
  content: string
  url: string
  sentiment: 'positive' | 'neutral' | 'negative'
  engagement_score: number
  published_at: string | null
  collected_at: string
}

export interface CollectionRun {
  id: number
  scope: string
  mode: 'live' | 'mock'
  status: 'running' | 'success' | 'failed'
  targets_processed: number
  records_created: number
  error_message: string
  started_at: string
  finished_at: string | null
}

export interface DashboardSummary {
  total_countries: number
  total_platforms: number
  total_price_points_24h: number
  new_price_points_24h: number
  active_promotions_7d: number
  social_posts_7d: number
  live_mode: boolean
  last_run: CollectionRun | null
  best_rate_per_card_type: {
    gift_card_type: string
    icon: string
    platform: string
    rate_percent: number
    currency: string
  }[]
  biggest_movers: {
    platform: string
    gift_card_type: string
    change_percent: number
    rate_percent: number
    currency: string
  }[]
}

export interface AgentStatus {
  has_exa: boolean
  has_llm: boolean
  live_mode: boolean
  llm_model: string
  llm_base_url: string
  collection_interval_minutes: number
  scheduler_enabled: boolean
}

export interface ContentIdeaItem {
  title: string
  description: string
  priority: string
}

export interface ContentIdeaCategory {
  category: string
  items: ContentIdeaItem[]
}

export interface CustomWatchExtraction {
  found: boolean
  headline?: string | null
  summary?: string | null
  key_facts: string[]
  confidence: number
}

export interface CustomWatchResult {
  url: string
  title: string
  extraction: CustomWatchExtraction | null
}
