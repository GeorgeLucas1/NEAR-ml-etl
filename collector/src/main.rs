use chrono::Utc;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::time::Duration;
use sysinfo::{Networks, System};
use tokio::time::sleep;

#[derive(Debug, Serialize, Deserialize)]
struct MetricsPayload {
    timestamp: String,
    cpu_usage: f32,
    cpu_temp: f32,
    ram_usage: f32,
    ram_total: f64,
    ram_used: f64,
    disk_read: f64,
    disk_write: f64,
    network_sent: f64,
    network_recv: f64,
    gpu_usage: f32,
    gpu_temp: f32,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();

    let api_url = std::env::var("API_URL").unwrap_or_else(|_| "http://localhost:8080".to_string());
    let interval_secs: u64 = std::env::var("INTERVAL_SECS")
        .unwrap_or_else(|_| "5".to_string())
        .parse()
        .unwrap_or(5);

    log::info!("PC Health Collector starting...");
    log::info!("API URL: {}", api_url);
    log::info!("Interval: {} seconds", interval_secs);

    let client = Client::new();
    let mut sys = System::new_all();
    let mut networks = Networks::new_with_refreshed_list();

    loop {
        sys.refresh_all();
        networks.refresh();

        let cpu_usage = sys.global_cpu_usage();
        let cpu_temp = get_cpu_temp();

        let ram_total = sys.total_memory() as f64;
        let ram_used = sys.used_memory() as f64;
        let ram_usage = if ram_total > 0.0 {
            (ram_used / ram_total) * 100.0
        } else {
            0.0
        };

        let (disk_read, disk_write) = get_disk_io();
        let (network_sent, network_recv) = get_network_io(&networks);
        let (gpu_usage, gpu_temp) = get_gpu_usage();

        let payload = MetricsPayload {
            timestamp: Utc::now().to_rfc3339(),
            cpu_usage,
            cpu_temp: cpu_temp.unwrap_or(0.0),
            ram_usage: ram_usage as f32,
            ram_total: ram_total / 1_073_741_824.0,
            ram_used: ram_used / 1_073_741_824.0,
            disk_read,
            disk_write,
            network_sent,
            network_recv,
            gpu_usage: gpu_usage.unwrap_or(0.0),
            gpu_temp: gpu_temp.unwrap_or(0.0),
        };

        match send_metrics(&client, &api_url, &payload).await {
            Ok(_) => {
                log::info!(
                    "Metrics sent: CPU {:.1}%, RAM {:.1}%, GPU {:?}%",
                    cpu_usage,
                    ram_usage,
                    gpu_usage
                );
            }
            Err(e) => {
                log::error!("Failed to send metrics: {}", e);
            }
        }

        sleep(Duration::from_secs(interval_secs)).await;
    }
}

async fn send_metrics(
    client: &Client,
    api_url: &str,
    payload: &MetricsPayload,
) -> Result<(), reqwest::Error> {
    let url = format!("{}/api/metrics/ingest", api_url);
    
    client
        .post(&url)
        .json(payload)
        .timeout(Duration::from_secs(10))
        .send()
        .await?;

    Ok(())
}

fn get_cpu_temp() -> Option<f32> {
    #[cfg(target_os = "linux")]
    {
        std::fs::read_to_string("/sys/class/thermal/thermal_zone0/temp")
            .ok()
            .and_then(|s| s.trim().parse::<f32>().ok())
            .map(|t| t / 1000.0)
    }

    #[cfg(not(target_os = "linux"))]
    {
        None
    }
}

fn get_disk_io() -> (f64, f64) {
    let disk_read: f64 = 0.0;
    let disk_write: f64 = 0.0;

    #[cfg(target_os = "linux")]
    {
        if let Ok(content) = std::fs::read_to_string("/proc/diskstats") {
            for line in content.lines().take(1) {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 10 {
                    if let (Ok(reads), Ok(writes)) = (
                        parts[5].parse::<u64>(),
                        parts[9].parse::<u64>(),
                    ) {
                        return (reads as f64 * 512.0, writes as f64 * 512.0);
                    }
                }
            }
        }
    }

    (disk_read, disk_write)
}

fn get_network_io(networks: &Networks) -> (f64, f64) {
    let mut sent: f64 = 0.0;
    let mut recv: f64 = 0.0;

    for (_name, data) in networks.iter() {
        recv += data.total_received() as f64;
        sent += data.total_transmitted() as f64;
    }

    (sent, recv)
}

fn get_gpu_usage() -> (Option<f32>, Option<f32>) {
    #[cfg(target_os = "linux")]
    {
        let usage = std::fs::read_to_string("/proc/driver/nvidia/gpus/0/utils_vbios")
            .ok()
            .is_some()
            .then_some(50.0_f32);
        (usage, None)
    }

    #[cfg(not(target_os = "linux"))]
    {
        (None, None)
    }
}
