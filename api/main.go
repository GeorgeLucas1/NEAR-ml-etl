package main

import (
	"flag"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/mux"

	"pc-health-api/internal/db"
	"pc-health-api/internal/handler"
	"pc-health-api/internal/ws"
)

func main() {
	var dbPath string
	var port string

	flag.StringVar(&dbPath, "db", "../data/metrics.db", "Path to SQLite database")
	flag.StringVar(&port, "port", "8080", "Server port")
	flag.Parse()

	log.Println("Starting PC Health API...")

	if err := db.Init(dbPath); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}
	defer db.Close()

	hub := ws.NewHub()
	go hub.Run()

	router := mux.NewRouter()

	router.Use(corsMiddleware)
	router.Use(loggingMiddleware)

	router.HandleFunc("/api/health", handler.HealthCheck).Methods("GET")

	router.HandleFunc("/api/metrics/ingest", handler.IngestMetrics).Methods("POST", "OPTIONS")
	router.HandleFunc("/api/metrics/latest", handler.GetLatestMetrics).Methods("GET")
	router.HandleFunc("/api/metrics/history", handler.GetMetricsHistory).Methods("GET")

	router.HandleFunc("/api/predict", handler.GetPrediction).Methods("GET")
	router.HandleFunc("/api/predict/forecast", handler.GetForecast).Methods("GET")
	router.HandleFunc("/api/model/info", handler.GetModelInfo).Methods("GET")

	router.HandleFunc("/api/anomalies", handler.GetAnomalies).Methods("GET")
	router.HandleFunc("/api/anomalies/history", handler.GetAnomaliesHistory).Methods("GET")
	router.HandleFunc("/api/baseline", handler.GetBaseline).Methods("GET")

	router.HandleFunc("/ws", func(w http.ResponseWriter, r *http.Request) {
		ws.HandleWebSocket(hub, w, r)
	}).Methods("GET")

	router.PathPrefix("/").Handler(http.FileServer(http.Dir("./static")))

	go broadcastLoop(hub)

	log.Printf("Server starting on :%s", port)
	log.Printf("WebSocket available at ws://localhost:%s/ws", port)
	log.Printf("API endpoints: http://localhost:%s/api/*", port)

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	if err := server.ListenAndServe(); err != nil {
		log.Fatalf("Server error: %v", err)
	}
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
	})
}

func broadcastLoop(hub *ws.Hub) {
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()

	for range ticker.C {
		m, err := db.GetLatestMetrics()
		if err == nil && hub.ClientCount() > 0 {
			metrics := map[string]interface{}{
				"timestamp": m.Timestamp,
				"cpu_usage": m.CPUUsage,
				"cpu_temp":  m.CPUtemp,
				"ram_usage": m.RAMUsage,
				"gpu_usage": m.GPUUsage,
			}
			hub.BroadcastMetrics(metrics)
		}
	}
}
