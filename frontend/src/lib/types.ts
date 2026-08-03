export interface User {
  id: number
  name: string
}

export interface Pool {
  id: number
  name: string
  contribution_amount: number
  member_cap: number
  invite_code: string
  current_cycle_number: number
  status: 'active' | 'completed'
  member_count: number
}

export interface Member {
  membership_id: number
  user_id: number
  name: string
  is_head: boolean
  has_won: boolean
  trust_score: number
}

export interface PoolDetail extends Pool {
  members: Member[]
}

export interface PoolPublic {
  id: number
  name: string
  contribution_amount: number
  member_cap: number
  current_cycle_number: number
  status: 'active' | 'completed'
  member_count: number
  head_name: string
  is_member: boolean
  has_pending_request: boolean
}

export interface JoinRequest {
  id: number
  pool_id: number
  user_id: number
  requester_name: string
  status: 'pending' | 'approved' | 'rejected'
}

export interface Cycle {
  id: number
  cycle_number: number
  status: 'collecting' | 'bidding_open' | 'resolved'
  winner_membership_id: number | null
  winner_name: string | null
  winning_bid_amount: number | null
  dividend_per_member: number | null
}

export interface LedgerEntry {
  id: number
  membership_id: number
  member_name: string
  cycle_id: number | null
  entry_type: 'contribution' | 'payout' | 'dividend'
  amount: number
  on_time: boolean | null
  created_at: string
}
