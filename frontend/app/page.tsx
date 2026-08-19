"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  Briefcase,
  CheckCircle2,
  Code2,
  Database,
  ExternalLink,
  FlaskConical,
  Info,
  Play,
  RefreshCw,
  Rss,
  Search,
  X,
} from "lucide-react";

const API =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

type Job = {
  id: number;
  title: string;
  company: string;
  location?: string | null;
  description?: string | null;
  url?: string | null;
  source_id?: number | null;
  source_name?: string | null;
  job_type?: string | null;
  published_at?: string | null;
};

type Source = {
  id: number;
  name: string;
  type: string;
  status: string;
  health_score: number;
  base_url?: string | null;
  last_run_at?: string | null;
  last_success_at?: string | null;
  last_failure_at?: string | null;
};

type Run = {
  id: number;
  source_id: number;
  status: string;
  jobs_found: number;
  jobs_added: number;
  jobs_updated?: number;
  jobs_duplicate: number;
  jobs_failed: number;
  error_count?: number;
  duration_ms?: number | null;
};

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);

  const [search, setSearch] = useState("");
  const [selectedSource, setSelectedSource] =
    useState<number | null>(null);

  const [detailsSource, setDetailsSource] =
    useState<Source | null>(null);

  const [loading, setLoading] = useState(true);
  const [runningSource, setRunningSource] =
    useState<number | null>(null);

  const [notice, setNotice] = useState<{
    text: string;
    type: "success" | "error";
  } | null>(null);

  // =========================================================
  // LOAD ALL DASHBOARD DATA
  // =========================================================

  async function loadData() {
    setLoading(true);

    try {
      const [jobsRes, sourcesRes, runsRes] =
        await Promise.all([
          fetch(`${API}/api/jobs`, {
            cache: "no-store",
          }),

          fetch(`${API}/api/sources`, {
            cache: "no-store",
          }),

          fetch(`${API}/api/ingestion/runs`, {
            cache: "no-store",
          }),
        ]);

      if (!jobsRes.ok) {
        throw new Error("Unable to load jobs");
      }

      const jobsData = await jobsRes.json();

      const sourcesData = sourcesRes.ok
        ? await sourcesRes.json()
        : [];

      const runsData = runsRes.ok
        ? await runsRes.json()
        : [];

      const jobsArray = Array.isArray(jobsData)
        ? jobsData
        : jobsData.items ||
          jobsData.jobs ||
          jobsData.data ||
          [];

      const sourcesArray = Array.isArray(
        sourcesData
      )
        ? sourcesData
        : sourcesData.items ||
          sourcesData.sources ||
          sourcesData.data ||
          [];

      const runsArray = Array.isArray(runsData)
        ? runsData
        : runsData.items ||
          runsData.runs ||
          runsData.data ||
          [];

      setJobs(jobsArray);
      setSources(sourcesArray);
      setRuns(runsArray);

      setNotice(null);
    } catch (error) {
      console.error(error);

      showNotice(
        "Could not connect to the JobPulse backend. Make sure FastAPI is running.",
        "error"
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  // =========================================================
  // NOTIFICATION
  // =========================================================

  function showNotice(
    text: string,
    type: "success" | "error"
  ) {
    setNotice({
      text,
      type,
    });

    setTimeout(() => {
      setNotice(null);
    }, 5000);
  }

  // =========================================================
  // SOURCE ORDER
  //
  // ALWAYS:
  // RSS -> API -> SANDBOX
  // =========================================================

  const orderedSources = useMemo(() => {
    const order: Record<string, number> = {
      RSS: 1,
      API: 2,
      SANDBOX: 3,
      BROWSER: 4,
    };

    return [...sources].sort((a, b) => {
      const aOrder =
        order[a.type.toUpperCase()] || 99;

      const bOrder =
        order[b.type.toUpperCase()] || 99;

      return aOrder - bOrder;
    });
  }, [sources]);

  // =========================================================
  // RUN SOURCE
  // =========================================================

  async function runSource(source: Source) {
    if (runningSource !== null) {
      return;
    }

    setRunningSource(source.id);

    try {
      const response = await fetch(
        `${API}/api/ingestion/run?source_id=${source.id}`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            "Could not start collection."
        );
      }

      showNotice(
        `${source.name} started. Job collection is running...`,
        "success"
      );

      /*
       * Backend uses BackgroundTasks.
       * Wait a few seconds and then reload.
       */

      setTimeout(async () => {
        await loadData();

        setRunningSource(null);

        showNotice(
          `${source.name} collection finished. Dashboard updated.`,
          "success"
        );
      }, 6000);
    } catch (error: any) {
      console.error(error);

      showNotice(
        error?.message ||
          "Something went wrong while collecting jobs.",
        "error"
      );

      setRunningSource(null);
    }
  }

  // =========================================================
  // RESET EVERYTHING
  //
  // Jobs + ingestion history are deleted.
  // Sources remain.
  // =========================================================

  async function resetData() {
    const confirmed = window.confirm(
      "Are you sure you want to reset JobPulse?\n\nThis will delete ALL collected jobs and ingestion history.\n\nYour RSS, API and Sandbox sources will remain configured."
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `${API}/api/ingestion/reset`,
        {
          method: "DELETE",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Reset failed."
        );
      }

      setJobs([]);
      setRuns([]);
      setSelectedSource(null);

      showNotice(
        "JobPulse has been reset. You can now start collecting from any source.",
        "success"
      );

      await loadData();
    } catch (error: any) {
      console.error(error);

      showNotice(
        error?.message ||
          "Could not reset JobPulse.",
        "error"
      );
    }
  }

  // =========================================================
  // FILTER JOBS
  // =========================================================

  const filteredJobs = useMemo(() => {
    const query = search
      .toLowerCase()
      .trim();

    return jobs.filter((job) => {
      const sourceMatches =
        selectedSource === null ||
        Number(job.source_id) ===
          Number(selectedSource);

      const searchableText = [
        job.title,
        job.company,
        job.location,
        job.job_type,
        job.source_name,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();

      const searchMatches =
        !query ||
        searchableText.includes(query);

      return (
        sourceMatches &&
        searchMatches
      );
    });
  }, [
    jobs,
    search,
    selectedSource,
  ]);

  // =========================================================
  // STATS
  // =========================================================

  const successfulRuns = runs.filter(
    (run) =>
      run.status?.toUpperCase() ===
      "SUCCESS"
  ).length;

  const totalFound = runs.reduce(
    (total, run) =>
      total + (run.jobs_found || 0),
    0
  );

  const totalAdded = runs.reduce(
    (total, run) =>
      total + (run.jobs_added || 0),
    0
  );

  const totalDuplicates = runs.reduce(
    (total, run) =>
      total + (run.jobs_duplicate || 0),
    0
  );

  // =========================================================
  // SOURCE RUN HELPERS
  // =========================================================

  function getSourceRuns(sourceId: number) {
    return runs
      .filter(
        (run) =>
          Number(run.source_id) ===
          Number(sourceId)
      )
      .sort((a, b) => b.id - a.id);
  }

  function getLatestRun(sourceId: number) {
    return getSourceRuns(sourceId)[0];
  }

  // =========================================================
  // VIEW JOBS FROM SOURCE
  // =========================================================

  function viewSourceJobs(sourceId: number) {
    setSelectedSource(sourceId);

    setTimeout(() => {
      document
        .getElementById("jobs")
        ?.scrollIntoView({
          behavior: "smooth",
        });
    }, 100);
  }

  // =========================================================
  // PAGE
  // =========================================================

  return (
    <main className="min-h-screen bg-[#070b14] text-white">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="sticky top-0 z-30 border-b border-white/10 bg-[#070b14]/95 backdrop-blur">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-blue-600 p-2.5 shadow-lg shadow-blue-600/20">
              <Briefcase size={21} />
            </div>

            <div>
              <h1 className="text-lg font-bold">
                JobPulse
              </h1>

              <p className="text-xs text-slate-500">
                Job Intelligence Engine
              </p>
            </div>

          </div>

          <div className="flex items-center gap-2">

            {/* RESET */}

            {/* <button
              onClick={resetData}
              className="rounded-lg border border-red-500/20 bg-red-500/5 px-4 py-2 text-sm text-red-400 transition hover:bg-red-500/10"
            >
              Reset Data
            </button> */}

            {/* REFRESH */}

            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/10 disabled:opacity-50"
            >
              <RefreshCw
                size={15}
                className={
                  loading
                    ? "animate-spin"
                    : ""
                }
              />

              Refresh
            </button>

          </div>

        </div>

      </header>

      {/* =====================================================
          NOTIFICATION
      ===================================================== */}

      {notice && (
        <div className="fixed right-5 top-20 z-50 max-w-md rounded-xl border border-white/10 bg-[#111827] p-4 shadow-2xl">

          <div className="flex gap-3">

            {notice.type === "success" ? (
              <CheckCircle2
                size={19}
                className="shrink-0 text-emerald-400"
              />
            ) : (
              <AlertCircle
                size={19}
                className="shrink-0 text-red-400"
              />
            )}

            <p className="text-sm text-slate-300">
              {notice.text}
            </p>

          </div>

        </div>
      )}

      <div className="mx-auto max-w-7xl px-6 py-10">

        {/* ===================================================
            HERO
        =================================================== */}

        <section className="mb-10">

          <div className="max-w-3xl">

            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/5 px-3 py-1 text-xs text-blue-400">

              <Activity size={13} />

              INGESTION MONITORING

            </div>

            <h2 className="text-4xl font-bold tracking-tight md:text-5xl">

              Find jobs.
              <br />

              <span className="text-blue-400">
                Understand your sources.
              </span>

            </h2>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400">

              JobPulse collects job information
              from RSS feeds, APIs and sandbox
              sources. It cleans, validates and
              deduplicates the data before making
              it available here.

            </p>

          </div>

        </section>

        {/* ===================================================
            STATS
        =================================================== */}

        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          <StatCard
            icon={<Briefcase size={19} />}
            title="Jobs Loaded"
            value={jobs.length}
            description="Currently available in the dashboard"
          />

          <StatCard
            icon={<Database size={19} />}
            title="Sources"
            value={sources.length}
            description="RSS, API and Sandbox sources"
          />

          <StatCard
            icon={<CheckCircle2 size={19} />}
            title="Successful Runs"
            value={successfulRuns}
            description="Completed ingestion runs"
          />

          <StatCard
            icon={<Activity size={19} />}
            title="New Jobs Added"
            value={totalAdded}
            description="Jobs saved across ingestion runs"
          />

        </section>

        {/* ===================================================
            HOW IT WORKS
        =================================================== */}

        <section className="mt-10 rounded-2xl border border-white/10 bg-white/[0.025] p-6">

          <div className="mb-6">

            <h3 className="text-xl font-semibold">
              How JobPulse works
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Four simple steps turn raw source data
              into searchable jobs.
            </p>

          </div>

          <div className="grid gap-6 md:grid-cols-4">

            <ProcessStep
              number="1"
              title="Collect"
              description="Connect to RSS feeds, APIs or the Sandbox."
            />

            <ProcessStep
              number="2"
              title="Clean"
              description="Convert different source formats into a common job format."
            />

            <ProcessStep
              number="3"
              title="Check"
              description="Validate required fields and remove duplicate jobs."
            />

            <ProcessStep
              number="4"
              title="Explore"
              description="Search and open the final collected job records."
            />

          </div>

        </section>

        {/* ===================================================
            SOURCES
        =================================================== */}

        <section className="mt-12">

          <div className="mb-6">

            <h3 className="text-2xl font-bold">
              Your Job Sources
            </h3>

            <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">

              Each source works differently.
              Select <strong>Collect</strong> to run
              that source, or select{" "}
              <strong>View Jobs</strong> to see only
              the jobs collected from it.

            </p>

          </div>

          {/* IMPORTANT:
              xl:grid-cols-3 guarantees all 3 cards
              appear side-by-side on a large screen.
          */}

          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">

            {orderedSources.map((source) => {

              const latestRun =
                getLatestRun(source.id);

              const health = Math.round(
                (source.health_score || 0) *
                  100
              );

              const isRunning =
                runningSource === source.id;

              return (
                <SourceCard
                  key={source.id}
                  source={source}
                  latestRun={latestRun}
                  health={health}
                  isRunning={isRunning}
                  onRun={() =>
                    runSource(source)
                  }
                  onViewJobs={() =>
                    viewSourceJobs(source.id)
                  }
                  onDetails={() =>
                    setDetailsSource(source)
                  }
                />
              );
            })}

          </div>

          {/* SAFETY MESSAGE IF NO SOURCES */}

          {orderedSources.length === 0 && (
            <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/5 p-8 text-center">

              <AlertCircle
                size={30}
                className="mx-auto text-yellow-400"
              />

              <h4 className="mt-3 font-semibold">
                No sources configured
              </h4>

              <p className="mt-1 text-sm text-slate-500">
                Check that the backend database
                contains your RSS, API and Sandbox
                sources.
              </p>

            </div>
          )}

        </section>

        {/* ===================================================
            JOBS
        =================================================== */}

        <section
          id="jobs"
          className="mt-12"
        >

          <div className="mb-6">

            <h3 className="text-2xl font-bold">
              Explore Jobs
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              Search and browse jobs collected by
              JobPulse.
            </p>

          </div>

          {/* SEARCH */}

          <div className="relative">

            <Search
              size={19}
              className="absolute left-4 top-3.5 text-slate-500"
            />

            <input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search by job title, company or location..."
              className="w-full rounded-xl border border-white/10 bg-white/[0.03] py-3.5 pl-11 pr-4 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500/60"
            />

          </div>

          {/* SOURCE FILTER */}

          {selectedSource !== null && (
            <div className="mt-4 flex items-center justify-between rounded-xl border border-blue-500/20 bg-blue-500/5 px-4 py-3">

              <div>

                <p className="text-xs text-blue-400">
                  SOURCE FILTER
                </p>

                <p className="mt-1 text-sm text-slate-300">

                  Showing jobs from{" "}

                  <strong>
                    {
                      sources.find(
                        (source) =>
                          Number(
                            source.id
                          ) ===
                          Number(
                            selectedSource
                          )
                      )?.name
                    }
                  </strong>

                </p>

              </div>

              <button
                onClick={() =>
                  setSelectedSource(null)
                }
                className="rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-white"
                title="Show all jobs"
              >
                <X size={17} />
              </button>

            </div>
          )}

          {/* COUNT */}

          <div className="my-5 flex items-center justify-between">

            <p className="text-sm text-slate-500">

              Showing{" "}

              <span className="font-medium text-slate-300">
                {filteredJobs.length}
              </span>{" "}

              jobs

            </p>

            {selectedSource !== null && (
              <button
                onClick={() =>
                  setSelectedSource(null)
                }
                className="text-xs text-blue-400 hover:text-blue-300"
              >
                Show all sources
              </button>
            )}

          </div>

          {/* JOB LIST */}

          <div className="space-y-3">

            {loading ? (
              <LoadingBox />
            ) : filteredJobs.length === 0 ? (
              <EmptyJobs />
            ) : (
              filteredJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                />
              ))
            )}

          </div>

        </section>

        {/* ===================================================
            COLLECTION SUMMARY
        =================================================== */}

        <section className="mt-12 pb-16">

          <div className="rounded-2xl border border-white/10 bg-white/[0.025] p-6">

            <div className="flex items-start justify-between">

              <div>

                <h3 className="text-xl font-semibold">
                  Collection Summary
                </h3>

                <p className="mt-1 text-sm text-slate-500">
                  What happened during your ingestion
                  runs.
                </p>

              </div>

              <Activity
                size={20}
                className="text-blue-400"
              />

            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-3">

              <SummaryCard
                label="Jobs Discovered"
                value={totalFound}
                explanation="Total records found by your sources"
              />

              <SummaryCard
                label="New Jobs Saved"
                value={totalAdded}
                explanation="Records successfully added to PostgreSQL"
              />

              <SummaryCard
                label="Duplicates Avoided"
                value={totalDuplicates}
                explanation="Existing records detected by deduplication"
              />

            </div>

          </div>

        </section>

      </div>

      {/* =====================================================
          SOURCE DETAILS MODAL
      ===================================================== */}

      {detailsSource && (
        <SourceDetails
          source={detailsSource}
          latestRun={getLatestRun(
            detailsSource.id
          )}
          onClose={() =>
            setDetailsSource(null)
          }
          onRun={() => {

            setDetailsSource(null);

            runSource(detailsSource);

          }}
        />
      )}

    </main>
  );
}

/* =========================================================
   STAT CARD
========================================================= */

function StatCard({
  icon,
  title,
  value,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  value: number;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-5">

      <div className="flex items-start justify-between">

        <div>

          <p className="text-sm text-slate-500">
            {title}
          </p>

          <p className="mt-2 text-3xl font-bold">
            {value}
          </p>

          <p className="mt-1 text-xs text-slate-600">
            {description}
          </p>

        </div>

        <div className="rounded-xl bg-blue-500/10 p-3 text-blue-400">
          {icon}
        </div>

      </div>

    </div>
  );
}

/* =========================================================
   PROCESS STEP
========================================================= */

function ProcessStep({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <div className="flex gap-4">

      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-blue-600 text-sm font-bold">
        {number}
      </div>

      <div>

        <h4 className="font-semibold">
          {title}
        </h4>

        <p className="mt-1 text-sm leading-6 text-slate-500">
          {description}
        </p>

      </div>

    </div>
  );
}

/* =========================================================
   SOURCE CARD
========================================================= */

function SourceCard({
  source,
  latestRun,
  health,
  isRunning,
  onRun,
  onViewJobs,
  onDetails,
}: {
  source: Source;
  latestRun?: Run;
  health: number;
  isRunning: boolean;
  onRun: () => void;
  onViewJobs: () => void;
  onDetails: () => void;
}) {
  const type =
    source.type.toUpperCase();

  const sourceInfo = {
    RSS: {
      icon: <Rss size={21} />,
      color:
        "bg-orange-500/10 text-orange-400",
      title: "RSS Feed",
      description:
        "Automatically reads published job updates from an RSS feed. Useful for collecting jobs from supported job boards.",
      button: "Collect from RSS",
    },

    API: {
      icon: <Code2 size={21} />,
      color:
        "bg-blue-500/10 text-blue-400",
      title: "API Source",
      description:
        "Gets structured information directly from an API and converts it into JobPulse's common job format.",
      button: "Collect from API",
    },

    SANDBOX: {
      icon: <FlaskConical size={21} />,
      color:
        "bg-purple-500/10 text-purple-400",
      title: "Sandbox Source",
      description:
        "A safe testing source that demonstrates the complete ingestion pipeline without depending on a live external service.",
      button: "Run Sandbox Test",
    },

  }[type] || {
    icon: <Database size={21} />,
    color:
      "bg-slate-500/10 text-slate-400",
    title: "Job Source",
    description:
      "External source connected to JobPulse.",
    button: "Collect Jobs",
  };

  return (
    <div className="flex h-full flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-6 transition hover:-translate-y-0.5 hover:border-white/20">

      {/* HEADER */}

      <div className="flex items-start justify-between">

        <div className="flex min-w-0 items-center gap-3">

          <div
            className={`shrink-0 rounded-xl p-3 ${sourceInfo.color}`}
          >
            {sourceInfo.icon}
          </div>

          <div className="min-w-0">

            <h4 className="truncate font-semibold">
              {source.name}
            </h4>

            <p className="mt-1 text-xs text-slate-500">
              {sourceInfo.title}
            </p>

          </div>

        </div>

        <div className="ml-3 flex shrink-0 items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">

          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

          {source.status || "UNKNOWN"}

        </div>

      </div>

      {/* DESCRIPTION */}

      <p className="mt-5 min-h-[88px] text-sm leading-6 text-slate-400">
        {sourceInfo.description}
      </p>

      {/* HEALTH */}

      <div className="mt-5">

        <div className="flex justify-between">

          <span className="text-xs text-slate-500">
            Source health
          </span>

          <span className="text-xs font-medium text-slate-300">
            {health}%
          </span>

        </div>

        <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/10">

          <div
            className="h-full rounded-full bg-emerald-500 transition-all"
            style={{
              width: `${Math.min(
                Math.max(health, 0),
                100
              )}%`,
            }}
          />

        </div>

      </div>

      {/* LATEST RUN */}

      <div className="mt-5 rounded-xl bg-white/[0.025] p-3">

        <p className="text-xs text-slate-600">
          Latest collection
        </p>

        {latestRun ? (
          <div className="mt-2 grid grid-cols-3 gap-2">

            <div>
              <p className="text-xs text-slate-600">
                Found
              </p>

              <p className="mt-1 text-sm font-medium text-slate-300">
                {latestRun.jobs_found}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                New
              </p>

              <p className="mt-1 text-sm font-medium text-emerald-400">
                +{latestRun.jobs_added}
              </p>
            </div>

            <div>
              <p className="text-xs text-slate-600">
                Duplicate
              </p>

              <p className="mt-1 text-sm font-medium text-slate-500">
                {latestRun.jobs_duplicate}
              </p>
            </div>

          </div>
        ) : (
          <p className="mt-2 text-sm text-slate-600">
            This source has not been run yet.
          </p>
        )}

      </div>

      {/* BUTTONS */}

      <div className="mt-auto pt-5 space-y-2">

        <button
          onClick={onRun}
          disabled={isRunning}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
        >

          {isRunning ? (
            <>
              <RefreshCw
                size={16}
                className="animate-spin"
              />

              Collecting...
            </>
          ) : (
            <>
              <Play size={16} />

              {sourceInfo.button}
            </>
          )}

        </button>

        <button
          onClick={onViewJobs}
          className="w-full rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm font-medium text-slate-300 transition hover:bg-white/10"
        >
          View Jobs From This Source
        </button>

      </div>

      {/* DETAILS */}

      <button
        onClick={onDetails}
        className="mt-4 flex w-full items-center justify-center gap-1 text-xs text-slate-500 transition hover:text-slate-300"
      >

        <Info size={13} />

        What does this source do?

      </button>

    </div>
  );
}

/* =========================================================
   JOB CARD
========================================================= */

function JobCard({
  job,
}: {
  job: Job;
}) {
  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.03] p-5 transition hover:border-blue-500/30">

      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

        <div className="min-w-0">

          <h4 className="text-base font-semibold leading-6">
            {job.title}
          </h4>

          <p className="mt-1 text-sm font-medium text-slate-300">
            {job.company || "Unknown company"}
          </p>

          <div className="mt-3 flex flex-wrap gap-2">

            {job.location && (
              <Tag>
                📍 {job.location}
              </Tag>
            )}

            {job.job_type && (
              <Tag>
                {job.job_type}
              </Tag>
            )}

            {job.source_name && (
              <Tag>
                {job.source_name}
              </Tag>
            )}

          </div>

        </div>

        {job.url && (
          <a
            href={job.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex shrink-0 items-center justify-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium transition hover:bg-blue-500"
          >

            View Original Job

            <ExternalLink size={15} />

          </a>
        )}

      </div>

    </article>
  );
}

/* =========================================================
   SOURCE DETAILS MODAL
========================================================= */

function SourceDetails({
  source,
  latestRun,
  onClose,
  onRun,
}: {
  source: Source;
  latestRun?: Run;
  onClose: () => void;
  onRun: () => void;
}) {
  const type =
    source.type.toUpperCase();

  let title = "Job Source";
  let explanation =
    "This source provides data to JobPulse.";

  if (type === "RSS") {
    title = "RSS Feed";

    explanation =
      "RSS allows JobPulse to read published job updates from a feed. When you collect this source, JobPulse downloads the feed and sends the records through the ingestion pipeline.";
  }

  if (type === "API") {
    title = "API Source";

    explanation =
      "The API source retrieves structured information from an external API. JobPulse converts the returned data into the same format used by the other sources.";
  }

  if (type === "SANDBOX") {
    title = "Sandbox Test Source";

    explanation =
      "The Sandbox is designed for testing. It allows you to demonstrate the complete ingestion process without depending on a live external job provider.";
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-5 backdrop-blur-sm">

      <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-white/10 bg-[#0d1422] shadow-2xl">

        {/* HEADER */}

        <div className="flex items-start justify-between border-b border-white/10 p-6">

          <div>

            <p className="text-xs uppercase tracking-wider text-blue-400">
              SOURCE INFORMATION
            </p>

            <h3 className="mt-2 text-xl font-semibold">
              {source.name}
            </h3>

            <p className="mt-1 text-sm text-slate-500">
              {title}
            </p>

          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-500 hover:bg-white/5 hover:text-white"
          >
            <X size={19} />
          </button>

        </div>

        {/* CONTENT */}

        <div className="space-y-5 p-6">

          <div>

            <h4 className="text-sm font-semibold">
              What does it do?
            </h4>

            <p className="mt-2 text-sm leading-6 text-slate-400">
              {explanation}
            </p>

          </div>

          <div className="grid grid-cols-2 gap-3">

            <InfoBox
              label="Source type"
              value={source.type}
            />

            <InfoBox
              label="Status"
              value={source.status}
            />

            <InfoBox
              label="Health"
              value={`${Math.round(
                (source.health_score ||
                  0) * 100
              )}%`}
            />

            <InfoBox
              label="Last run"
              value={
                source.last_run_at
                  ? new Date(
                      source.last_run_at
                    ).toLocaleString()
                  : "Never"
              }
            />

          </div>

          {source.base_url && (
            <div className="rounded-xl bg-white/[0.03] p-4">

              <p className="text-xs text-slate-600">
                Source endpoint
              </p>

              <p className="mt-1 break-all text-xs text-slate-400">
                {source.base_url}
              </p>

            </div>
          )}

          {latestRun && (
            <div className="rounded-xl bg-white/[0.03] p-4">

              <p className="text-xs text-slate-500">
                Latest collection result
              </p>

              <div className="mt-3 grid grid-cols-3 gap-3">

                <Result
                  label="Found"
                  value={
                    latestRun.jobs_found
                  }
                />

                <Result
                  label="Added"
                  value={
                    latestRun.jobs_added
                  }
                />

                <Result
                  label="Duplicates"
                  value={
                    latestRun.jobs_duplicate
                  }
                />

              </div>

            </div>
          )}

        </div>

        {/* FOOTER */}

        <div className="flex gap-3 border-t border-white/10 p-6">

          <button
            onClick={onClose}
            className="flex-1 rounded-lg border border-white/10 bg-white/5 py-3 text-sm text-slate-300 hover:bg-white/10"
          >
            Close
          </button>

          <button
            onClick={onRun}
            className="flex-1 rounded-lg bg-blue-600 py-3 text-sm font-semibold hover:bg-blue-500"
          >
            Collect From Source
          </button>

        </div>

      </div>

    </div>
  );
}

/* =========================================================
   SMALL COMPONENTS
========================================================= */

function Tag({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <span className="rounded-md bg-white/5 px-2.5 py-1 text-xs text-slate-400">
      {children}
    </span>
  );
}

function SummaryCard({
  label,
  value,
  explanation,
}: {
  label: string;
  value: number;
  explanation: string;
}) {
  return (
    <div className="rounded-xl bg-white/[0.03] p-5">

      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-3xl font-bold">
        {value}
      </p>

      <p className="mt-1 text-xs leading-5 text-slate-600">
        {explanation}
      </p>

    </div>
  );
}

function InfoBox({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl bg-white/[0.03] p-3">

      <p className="text-xs text-slate-600">
        {label}
      </p>

      <p className="mt-1 break-words text-sm font-medium text-slate-300">
        {value}
      </p>

    </div>
  );
}

function Result({
  label,
  value,
}: {
  label: string;
  value: number;
}) {
  return (
    <div>

      <p className="text-xs text-slate-600">
        {label}
      </p>

      <p className="mt-1 text-lg font-semibold">
        {value}
      </p>

    </div>
  );
}

function LoadingBox() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-12 text-center">

      <RefreshCw
        size={25}
        className="mx-auto animate-spin text-blue-400"
      />

      <p className="mt-4 text-sm text-slate-500">
        Loading jobs...
      </p>

    </div>
  );
}

function EmptyJobs() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-12 text-center">

      <Briefcase
        size={35}
        className="mx-auto text-slate-700"
      />

      <h4 className="mt-4 font-medium text-slate-400">
        No jobs found
      </h4>

      <p className="mt-1 text-sm text-slate-600">
        Try another search or collect jobs from
        one of the sources above.
      </p>

    </div>
  );
}