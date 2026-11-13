import React from "react";
import EventBreakdownClient from "./EventBreakdownClient";

const STATIC_EVENT_IDS = [
  "ev_fb_ars_che",
  "ev_fb_rma_val",
  "ev_bb_bos_nyk",
  "ev_ten_alc_sin",
  "ev_ten_swi_sab",
  "ev_hk_edm_cgy",
  "ev_tt_nov_kow",
];

export function generateStaticParams() {
  return STATIC_EVENT_IDS.map((id) => ({ id }));
}

export default function EventBreakdownPage() {
  return <EventBreakdownClient />;
}
