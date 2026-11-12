/** Friendly aliases over the generated OpenAPI types (src/types/api.ts). Never hand-written. */
import type { components } from '@/types/api';

type S = components['schemas'];

export type Me = S['MeResponse'];
export type Role = Me['role'];
export type Rules = S['RulesResponse'];

export type Dashboard = S['DashboardResponse'];
export type JourneyCard = S['JourneyCard'];
export type JourneyState = JourneyCard['effective_state'];
export type BookingView = S['BookingView'];
export type OutcomeView = S['OutcomeView'];
export type OutcomeResult = OutcomeView['result'];
export type LadderRung = S['LadderRung'];
export type EventItem = S['EventItem'];
export type Stats = S['Stats'];

export type SlotsResponse = S['SlotsResponse'];
export type SlotDay = S['SlotDay'];
export type SlotTime = S['SlotTime'];
export type BookingResponse = S['BookingResponse'];
export type StateResponse = S['StateResponse'];

export type Inbox = S['InboxResponse'];
export type NotificationItem = S['NotificationItem'];
export type Leaderboard = S['LeaderboardResponse'];
export type LeaderboardRow = S['LeaderboardRow'];

export type Schedule = S['ScheduleResponse'];
export type ScheduleItem = S['ScheduleItem'];
export type Chip = ScheduleItem['chip'];
export type InterviewDetail = S['InterviewDetail'];
export type InterviewerOutcome = S['InterviewerOutcome'];
export type OutcomeCreate = S['OutcomeCreate'];
export type OutcomeEdit = S['OutcomeEdit'];
export type OutcomeResponse = S['OutcomeResponse'];
export type Availability = S['AvailabilityResponse'];
export type AvailabilityWindow = S['AvailabilityWindow'];
export type AvailabilitySlot = S['AvailabilitySlot'];
export type WindowCreate = S['WindowCreate'];
export type WindowCreated = S['WindowCreated'];
export type SlotPatched = S['SlotPatched'];

export type Tracker = S['TrackerResponse'];
export type TrackerTab = Tracker['tab'];
export type NotBookedRow = S['NotBookedRow'];
export type BookedRow = S['BookedRow'];
export type AwaitingRow = S['AwaitingRow'];
export type ResultRow = S['ResultRow'];
export type NudgeRequest = S['NudgeRequest'];
export type NudgeResponse = S['NudgeResponse'];
export type FlagCreate = S['FlagCreate'];
export type FlagCreated = S['FlagCreated'];
export type FlagDecision = S['FlagDecision'];
export type FlagDecided = S['FlagDecided'];
export type ReassignOptions = S['ReassignOptions'];
export type ReassignResponse = S['ReassignResponse'];
export type SentResponse = S['SentResponse'];

export type RegisterRequest = S['RegisterRequest'];
export type RegistrationOptions = S['RegistrationOptions'];
