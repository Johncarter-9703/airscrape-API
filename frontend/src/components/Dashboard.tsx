"use client";

import React, { useState, useEffect } from "react";
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell, Area, ComposedChart
} from "recharts";
import { 
  TrendingUp, TrendingDown, Activity, AlertTriangle, ShieldCheck, Database, Plane, BarChart3, ChevronRight, Info, Search
} from "lucide-react";
import { fetchRouteLeadTime } from "@/lib/api";

export default function Dashboard({ 
  initialSummary, 
  initialTimeseries, 
  initialRoutes, 
  initialAnomalies, 
  initialHealth 
}: any) {
  const [selectedRoute, setSelectedRoute] = useState(initialRoutes[0]?.route_code);
  const [leadTimeData, setLeadTimeData] = useState<any[]>([]);
  const [isLoadingCurve, setIsLoadingCurve] = useState(false);
  const [expandedRoute, setExpandedRoute] = useState<string | null>(null);

  useEffect(() => {
    if (selectedRoute) {
      setIsLoadingCurve(true);
      fetchRouteLeadTime(selectedRoute)
        .then(res => setLeadTimeData(res.data))
        .catch(err => console.error(err))
        .finally(() => setIsLoadingCurve(false));
    }
  }, [selectedRoute]);

  const currentApix = initialSummary.current_apix.toFixed(1);
  const isPositive = initialSummary.delta_24h > 0;
  
  // Dynamic insight generation
  const worstRoute = initialRoutes.reduce((prev: any, current: any) => (prev.price_change_percentage > current.price_change_percentage) ? prev : current, initialRoutes[0]);
  
  return (
    <div className="space-y-10 pb-16">
      
      {/* 1. HERO SECTION */}
      <section id="overview" className="flex flex-col lg:flex-row gap-8 items-start justify-between border-b border-[#1F222E] pb-8 pt-6 scroll-mt-24">
        <div className="max-w-2xl">
          <h2 className="text-[#94A3B8] text-xs font-semibold tracking-widest uppercase mb-4">Airfare Market Index (APIx)</h2>
          <div className="flex items-baseline gap-6 mb-4">
            <div className="text-6xl font-light tracking-tight text-[#F8FAFC]">
              {currentApix}
            </div>
            <div className="flex flex-col">
              <div className={`flex items-center text-xl font-medium ${isPositive ? 'text-[#F43F5E]' : 'text-[#10B981]'}`}>
                {isPositive ? <TrendingUp className="w-5 h-5 mr-1" /> : <TrendingDown className="w-5 h-5 mr-1" />}
                {isPositive ? '+' : ''}{initialSummary.delta_24h.toFixed(1)}%
              </div>
              <span className="text-[#64748B] text-sm">vs previous period</span>
            </div>
          </div>
          <p className="text-[#CBD5E1] text-lg leading-relaxed font-light border-l-2 border-[#38BDF8] pl-4">
            Domestic airfare prices remain <span className="font-medium text-[#F8FAFC]">{isPositive ? 'elevated' : 'depressed'}</span>, driven primarily by short-notice bookings on <span className="font-medium text-[#F8FAFC]">{worstRoute.origin}–{worstRoute.destination}</span>.
          </p>
        </div>
        
        {/* Market Status Side Panel */}
        <div className="bg-[#11131A] border border-[#1F222E] rounded p-5 min-w-[280px]">
          <h3 className="text-[#94A3B8] text-xs font-semibold uppercase mb-4 tracking-wider">Market Status</h3>
          <div className="space-y-4 text-sm">
            <div className="flex justify-between items-center">
              <span className="text-[#64748B]">Pressure</span>
              <span className={`font-medium ${isPositive ? 'text-[#F43F5E]' : 'text-[#10B981]'}`}>{isPositive ? 'Elevated' : 'Subdued'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#64748B]">Data Confidence</span>
              <span className="font-medium text-[#F8FAFC]">{(initialSummary.data_quality_percentage).toFixed(1)}%</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-[#64748B]">Active Sources</span>
              <span className="font-medium text-[#F8FAFC]">{initialHealth.active_sources} / 7</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. COMPACT KPIs */}
      <section className="flex flex-wrap gap-x-12 gap-y-4 text-sm border-b border-[#1F222E] pb-6">
        <div className="flex flex-col">
          <span className="text-[#64748B] uppercase tracking-wider text-[10px] mb-1">Total Observations</span>
          <span className="text-xl font-medium text-[#F8FAFC]">{initialHealth.total_quotes_parsed.toLocaleString()}</span>
        </div>
        <div className="w-px h-10 bg-[#1F222E] hidden sm:block"></div>
        <div className="flex flex-col">
          <span className="text-[#64748B] uppercase tracking-wider text-[10px] mb-1">Data Quality</span>
          <span className="text-xl font-medium text-[#10B981]">{initialSummary.data_quality_percentage.toFixed(1)}%</span>
        </div>
        <div className="w-px h-10 bg-[#1F222E] hidden sm:block"></div>
        <div className="flex flex-col">
          <span className="text-[#64748B] uppercase tracking-wider text-[10px] mb-1">Flagged Records</span>
          <span className="text-xl font-medium text-[#F59E0B]">{initialHealth.flagged_rate_percentage.toFixed(1)}%</span>
        </div>
        <div className="w-px h-10 bg-[#1F222E] hidden sm:block"></div>
        <div className="flex flex-col">
          <span className="text-[#64748B] uppercase tracking-wider text-[10px] mb-1">Last Sync</span>
          <span className="text-xl font-medium text-[#F8FAFC]">Just now</span>
        </div>
      </section>

      {/* 3. MAIN MARKET TREND */}
      <section id="market-trends" className="grid grid-cols-1 lg:grid-cols-4 gap-6 scroll-mt-24">
        <div className="lg:col-span-3 bg-[#11131A] border border-[#1F222E] rounded p-6 relative">
          <div className="flex justify-between items-center mb-8">
            <div>
              <h3 className="text-lg font-medium text-[#F8FAFC]">APIx Market Trend</h3>
              <p className="text-[#64748B] text-sm mt-1">30-day airfare price movement across the domestic route basket.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs bg-[#1F222E] text-[#94A3B8] px-3 py-1 rounded">30D</span>
            </div>
          </div>
          
          <div className="h-[350px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={initialTimeseries.data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1F222E" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  tick={{ fontSize: 11, fill: '#64748B' }}
                  axisLine={false}
                  tickLine={false}
                  dy={10}
                />
                <YAxis 
                  domain={['dataMin - 2', 'dataMax + 2']} 
                  tick={{ fontSize: 11, fill: '#64748B' }}
                  axisLine={false}
                  tickLine={false}
                />
                <RechartsTooltip 
                  contentStyle={{ backgroundColor: '#090A0F', borderColor: '#1F222E', color: '#F8FAFC', fontSize: '12px' }}
                  itemStyle={{ color: '#38BDF8' }}
                  labelFormatter={(val) => new Date(val).toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric' })}
                />
                <ReferenceLine y={100} stroke="#475569" strokeDasharray="3 3" label={{ position: 'insideTopLeft', value: 'Base Index (100)', fill: '#64748B', fontSize: 11 }} />
                
                {/* Confidence Band (mocking high/low using composed area) */}
                <Area 
                  type="monotone" 
                  dataKey="index_value" 
                  fill="#38BDF8" 
                  fillOpacity={0.05} 
                  stroke="none"
                />
                
                <Line 
                  type="monotone" 
                  dataKey="index_value" 
                  stroke="#38BDF8" 
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4, fill: '#090A0F', stroke: '#38BDF8', strokeWidth: 2 }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Intelligence Side Panel */}
        <div className="bg-[#11131A] border border-[#1F222E] rounded p-6 flex flex-col">
          <h3 className="text-[#94A3B8] text-xs font-semibold uppercase mb-6 tracking-wider flex items-center gap-2">
            <Activity className="w-3 h-3 text-[#38BDF8]" />
            Market Signal
          </h3>
          
          <div className="space-y-6 flex-1">
            <div className="pb-4 border-b border-[#1F222E]">
              <div className="flex items-start gap-3">
                <TrendingUp className="w-5 h-5 text-[#F43F5E] mt-0.5" />
                <div>
                  <p className="text-[#F8FAFC] text-sm font-medium leading-snug">Short-notice fares increased by 8.4% across metro routes.</p>
                </div>
              </div>
            </div>

            <div className="pb-4 border-b border-[#1F222E]">
              <p className="text-[#64748B] text-xs uppercase mb-1">Primary Contributor</p>
              <p className="text-[#F8FAFC] text-sm font-medium">{worstRoute.origin} → {worstRoute.destination}</p>
            </div>

            <div className="pb-4">
              <p className="text-[#64748B] text-xs uppercase mb-1">Highest Volatility</p>
              <p className="text-[#F8FAFC] text-sm font-medium">T+1 Bookings (Next-day)</p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. TWO-COLUMN ANALYTICAL SECTION */}
      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Booking Window (Lead-Time Elasticity) */}
        <div className="bg-[#11131A] border border-[#1F222E] rounded p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-lg font-medium text-[#F8FAFC]">Booking Window Intelligence</h3>
              <p className="text-[#64748B] text-sm mt-1">How airfare changes based on days before departure.</p>
            </div>
            <select 
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
              className="text-xs bg-[#090A0F] border border-[#1F222E] text-[#F8FAFC] rounded py-1.5 pl-3 pr-8 focus:outline-none focus:border-[#38BDF8]"
            >
              {initialRoutes.map((r: any) => (
                <option key={r.route_code} value={r.route_code}>{r.route_code}</option>
              ))}
            </select>
          </div>
          
          <div className="h-64 mb-4">
            {!isLoadingCurve && leadTimeData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={leadTimeData} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#1F222E" />
                  <XAxis dataKey="lead_time_bucket" tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} dy={10} />
                  <YAxis tick={{ fontSize: 11, fill: '#64748B' }} axisLine={false} tickLine={false} />
                  <RechartsTooltip 
                    cursor={{fill: '#1F222E'}}
                    contentStyle={{ backgroundColor: '#090A0F', borderColor: '#1F222E', color: '#F8FAFC', fontSize: '12px' }}
                    formatter={(val) => [`₹${val}`, 'Fare']}
                  />
                  <Bar dataKey="representative_fare" radius={[2, 2, 0, 0]}>
                    {leadTimeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={index === 0 ? '#F43F5E' : index === leadTimeData.length - 1 ? '#10B981' : '#334155'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-[#64748B] text-sm">Loading curve data...</div>
            )}
          </div>
          <p className="text-[#94A3B8] text-xs flex items-center gap-2">
            <Info className="w-3 h-3 text-[#38BDF8]" />
            Fares increase sharply within the final 7 days before departure.
          </p>
        </div>

        {/* System Health Compact Panel */}
        <div className="bg-[#11131A] border border-[#1F222E] rounded p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-medium text-[#F8FAFC] mb-6">Infrastructure Health</h3>
            
            <div className="grid grid-cols-2 gap-8">
              <div>
                <p className="text-[#64748B] text-xs uppercase mb-3">Pipeline Status</p>
                <ul className="space-y-3 text-sm">
                  {['Ingestion', 'Refinement', 'Validation', 'Anomaly Engine', 'Index Engine'].map((stage, i) => (
                    <li key={i} className="flex justify-between items-center">
                      <span className="text-[#94A3B8]">{stage}</span>
                      <span className="text-[#10B981] text-xs">Operational</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div>
                <p className="text-[#64748B] text-xs uppercase mb-3">Data Sources</p>
                <ul className="space-y-3 text-sm">
                  {['MakeMyTrip', 'Cleartrip', 'Yatra', 'Goibibo', 'Ixigo', 'Air India', 'IndiGo'].map((src, i) => (
                    <li key={i} className="flex justify-between items-center">
                      <span className="text-[#94A3B8]">{src}</span>
                      <div className="w-2 h-2 rounded-full bg-[#10B981]"></div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-4 border-t border-[#1F222E] text-xs text-[#64748B] flex justify-between">
            <span>Throughput: ~150 req/min</span>
            <span>Latency: 42ms</span>
          </div>
        </div>

      </section>

      {/* 5. ROUTE PERFORMANCE TABLE */}
      <section id="routes" className="bg-[#11131A] border border-[#1F222E] rounded overflow-hidden scroll-mt-24">
        <div className="p-5 border-b border-[#1F222E]">
          <h3 className="text-lg font-medium text-[#F8FAFC]">Route Performance Basket</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-[10px] text-[#64748B] uppercase tracking-wider bg-[#090A0F]">
              <tr>
                <th className="px-6 py-4 font-medium">Route</th>
                <th className="px-6 py-4 font-medium">Weight</th>
                <th className="px-6 py-4 font-medium">Base (PO)</th>
                <th className="px-6 py-4 font-medium">Current (PT)</th>
                <th className="px-6 py-4 font-medium">Change</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1F222E]">
              {initialRoutes.map((route: any) => (
                <React.Fragment key={route.route_code}>
                  <tr 
                    onClick={() => setExpandedRoute(expandedRoute === route.route_code ? null : route.route_code)}
                    className="hover:bg-[#1A1D27] transition-colors group cursor-pointer"
                  >
                    <td className="px-6 py-4 font-medium text-[#F8FAFC] flex items-center gap-3">
                      {route.origin} <ChevronRight className="w-3 h-3 text-[#64748B]"/> {route.destination}
                    </td>
                    <td className="px-6 py-4 text-[#94A3B8]">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-[#1F222E] rounded overflow-hidden">
                          <div className="h-full bg-[#334155]" style={{ width: `${route.weight * 100}%` }}></div>
                        </div>
                        <span className="text-xs">{(route.weight * 100).toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-[#64748B]">₹{route.base_fare_p0}</td>
                    <td className="px-6 py-4 font-medium text-[#F8FAFC]">₹{route.current_representative_fare}</td>
                    <td className="px-6 py-4 flex items-center justify-between">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        route.price_change_percentage > 0 ? 'bg-[#F43F5E]/10 text-[#F43F5E]' : 
                        route.price_change_percentage < 0 ? 'bg-[#10B981]/10 text-[#10B981]' : 'bg-[#1F222E] text-[#94A3B8]'
                      }`}>
                        {route.price_change_percentage > 0 ? '+' : ''}{route.price_change_percentage.toFixed(1)}%
                      </span>
                      <span className="text-[#64748B] text-[10px] uppercase tracking-wide group-hover:text-[#38BDF8] transition-colors">
                        {expandedRoute === route.route_code ? 'Close' : 'View OTAs'}
                      </span>
                    </td>
                  </tr>
                  
                  {expandedRoute === route.route_code && (
                    <tr className="bg-[#090A0F]">
                      <td colSpan={5} className="px-6 py-4 border-t-0">
                        <div className="flex flex-wrap gap-4 pt-1 pb-2">
                          {route.source_prices && Object.keys(route.source_prices).length > 0 ? (
                            Object.entries(route.source_prices).map(([source, price]) => (
                              <div key={source} className="flex flex-col bg-[#11131A] border border-[#1F222E] rounded px-3 py-2 min-w-[120px]">
                                <span className="text-[#64748B] text-[10px] uppercase tracking-wider mb-1">{source}</span>
                                <span className="text-[#F8FAFC] font-medium text-sm">₹{Number(price).toFixed(2)}</span>
                              </div>
                            ))
                          ) : (
                            <div className="text-[#64748B] text-xs py-2 italic">Awaiting source data from aggregator...</div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* 6. ANOMALY MONITOR FEED */}
      <section id="anomalies" className="bg-[#11131A] border border-[#1F222E] rounded flex flex-col scroll-mt-24">
        <div className="p-5 border-b border-[#1F222E] flex justify-between items-center bg-[#090A0F]">
          <h3 className="text-lg font-medium text-[#F8FAFC]">Anomaly Monitor</h3>
          <div className="flex gap-2 text-xs">
            <button className="bg-[#1F222E] text-[#F8FAFC] px-3 py-1 rounded">All</button>
            <button className="text-[#64748B] hover:text-[#F8FAFC] px-3 py-1 transition-colors">Critical</button>
            <button className="text-[#64748B] hover:text-[#F8FAFC] px-3 py-1 transition-colors">Conflicts</button>
          </div>
        </div>
        <div className="p-6">
          <div className="space-y-6 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-[#1F222E] before:to-transparent">
            {initialAnomalies.length > 0 ? initialAnomalies.map((anomaly: any, i: number) => (
              <div key={anomaly.id} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                {/* Timeline Node */}
                <div className="flex items-center justify-center w-10 h-10 rounded-full border-4 border-[#11131A] bg-[#1F222E] group-hover:bg-[#F59E0B] text-[#64748B] group-hover:text-[#090A0F] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow transition-colors z-10">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                
                {/* Content Card */}
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded border border-[#1F222E] bg-[#090A0F] shadow-sm">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <span className="text-[10px] font-semibold uppercase tracking-wider text-[#F59E0B] mb-1 block">Price Outlier</span>
                      <div className="flex items-center gap-2">
                        <span className="text-[#F8FAFC] font-medium text-sm">{anomaly.route}</span>
                        <span className="text-[#64748B] text-xs">•</span>
                        <span className="text-[#94A3B8] text-xs">{anomaly.source}</span>
                      </div>
                    </div>
                    <span className="text-xs text-[#64748B]">{anomaly.date}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm mt-4 pt-4 border-t border-[#1F222E]">
                    <div>
                      <p className="text-[#64748B] text-xs mb-1">Observed</p>
                      <p className="text-[#F8FAFC] font-bold">₹{Number(anomaly.raw_fare).toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-[#64748B] text-xs mb-1">Z-Score</p>
                      <p className="text-[#F43F5E] font-mono">{anomaly.z_score.toFixed(1)}</p>
                    </div>
                  </div>
                </div>
              </div>
            )) : (
              <div className="text-center py-12 text-[#64748B] text-sm">
                No active anomalies in the data stream.
              </div>
            )}
          </div>
        </div>
      </section>

    </div>
  );
}
