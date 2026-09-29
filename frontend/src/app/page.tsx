import Dashboard from "@/components/Dashboard";
import { fetchSummary, fetchTimeseries, fetchRoutes, fetchRecentAnomalies, fetchSystemHealth } from "@/lib/api";
import { Plane, Settings, Clock } from "lucide-react";

export default async function Home() {
  let summary = null;
  let timeseries = null;
  let routes = null;
  let anomalies = null;
  let health = null;
  
  try {
    const data = await Promise.all([
      fetchSummary(),
      fetchTimeseries("30d", "daily"),
      fetchRoutes(),
      fetchRecentAnomalies(5),
      fetchSystemHealth()
    ]);
    summary = data[0];
    timeseries = data[1];
    routes = data[2];
    anomalies = data[3];
    health = data[4];
  } catch (error) {
    console.error("Failed to load initial data", error);
  }

  return (
    <main className="min-h-screen bg-[#090A0F] text-[#F8FAFC] font-sans selection:bg-[#38BDF8] selection:text-[#090A0F]">
      {/* Top Navigation */}
      <nav className="border-b border-[#1F222E] bg-[#090A0F]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-[1400px] mx-auto px-6 h-14 flex items-center justify-between">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="bg-[#11131A] p-1.5 rounded border border-[#1F222E]">
              <Plane className="w-4 h-4 text-[#38BDF8]" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-wide flex items-center gap-2">
                AIR-SCRAPE
                <span className="text-[#334155]">/</span>
                <span className="text-[#94A3B8] font-normal">Intelligence Platform</span>
              </h1>
            </div>
          </div>

          {/* Center Links */}
          <div className="hidden md:flex items-center gap-8 text-xs font-medium text-[#64748B]">
            <a href="#overview" className="text-[#F8FAFC] hover:text-[#F8FAFC] transition-colors">Overview</a>
            <a href="#routes" className="hover:text-[#F8FAFC] transition-colors">Routes</a>
            <a href="#market-trends" className="hover:text-[#F8FAFC] transition-colors">Market Trends</a>
            <a href="#anomalies" className="hover:text-[#F8FAFC] transition-colors">Anomalies</a>
          </div>

          {/* Right Status */}
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2 text-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#10B981] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#10B981]"></span>
              </span>
              <span className="text-[#94A3B8] flex items-center gap-1">
                LIVE DATA <span className="hidden sm:inline">| Updated just now</span>
              </span>
            </div>
            <div className="h-4 w-px bg-[#1F222E]"></div>
            <button className="text-[#64748B] hover:text-[#F8FAFC] transition-colors">
              <Settings className="w-4 h-4" />
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content Area */}
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        {summary ? (
          <Dashboard 
            initialSummary={summary} 
            initialTimeseries={timeseries}
            initialRoutes={routes}
            initialAnomalies={anomalies}
            initialHealth={health}
          />
        ) : (
          <div className="flex items-center justify-center h-64 border border-[#1F222E] rounded bg-[#11131A]">
            <div className="text-center">
              <div className="w-6 h-6 border-2 border-[#38BDF8] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-[#94A3B8] text-sm">Connecting to Data Engine...</p>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
