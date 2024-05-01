#include <stdio.h>
#include <string.h>
#include <lwip/sockets.h>
#include <errno.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/semphr.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "nvs_flash.h"
#include "lwip/err.h"
#include "lwip/sys.h"
#include <stdlib.h>
#include "Arduino.h"
#include "cpp_header.h"
#include "ds18b20.h"
#include <esp_system.h>
#include "tds_sensor.h"
#include "esp_console.h"
#include "lwip/apps/sntp.h"
#include <time.h>
#include "esp_timer.h"
#include "soc/clk_tree_defs.h"

/* Constants*/
#define PORT_NUMBER 8001
#define MAX_DATA_SIZE 256
#define SAMPLE_SIZE 10
#define SENSOR_STR_SIZE 256  // Max size for each sensor string
#define SENSOR_COUNT 4     // Number of sensors
#define TEMP_BUS 23 // Current pin for temp sensor
#define LED 2
#define HIGH2 1
#define LOW2 0
#define digitalWrite gpio_set_level
#define WAITING 0
#define COLLECTING_DATA 1
#define SENT_TIME 2
#define SENDING_DATA 3


/* Socket server parameters*/
static char TAG[] = "socket server";
const char* ssid = ""; // Set your WiFi SSID
const char* pass = ""; // Set your WiFi Password
int client_socket; // For the client socket of the raspberry pi
int retry_num = 0; // Tracks the number of times esp32 is unable to connect to access point

/* Buffers for sending data through the socket server*/
uint8_t dataBuffer[SENSOR_STR_SIZE * SENSOR_COUNT]; // Buffer for sensor data
uint8_t timeDataBuffer[SENSOR_STR_SIZE * 2]; // Buffer for both elapsed times

// Global variables
long int rIndex1;
long int rIndex2;
volatile float sharedTDSValue;
volatile float cTemp;
volatile float phValue;
volatile float turbidity;
int accept_counter = 0;

/* Data buffers for the sensors */
float temperData[100];
float tdsData[100];
float pHData[100];
float turbData[100];
volatile int dbIndex = 0; // Index for the sensor data buffers

/* Conditions for triggering state change*/
int state = 0; // State of esp32 in the state machine
bool client_connected = false; // Status of client connection
bool submerged = false;  // True if module is underwater
bool collectData = false; // True if currently collecting data
bool SCM_received = false; // True if the "START_COLLECTION" message has been received
bool SCC_sent = false; // True if the "STARTING_COLLECTION" confirmation has been sent
bool DC_performed = false; // True if data collection has been completed
bool STM_received = false; // True if "SEND_TIME" message has been received
bool DI_received = false; // True if data indexes have been received
bool processDisrupted = false;

/* Variables for collecting elapsed time */
uint64_t time_DCCreceived; // Time when the "START_COLLECTION" was received
uint64_t time_submerged; // Time when WQM entered the water
uint64_t time_emerged; // Time when WQM emerged from water
float elapsedTime = 0; // the amount of time WQ module was under water
float elapsedTime2 = 0; // the amount of time between the DC command being received and WQ first goes into water
uint64_t current_time;



DeviceAddress tempSensors[2];
TimerHandle_t timerHandle;

void setState() {
	/* Changes the state of the esp32 in the state machine. Determines what message to
	   the raspberry pi. It's called after reading ReadMessage is called*/
	if (DI_received) {
		state = 5;
	}
	else if (STM_received) {
		state = 4;
	}
	else if (DC_performed && client_connected) {
		state = 3;
	}
	else if (SCM_received) {
		state = 2;
	}
	else if (client_connected) {
		state = 1;
	}
	else {
		state = 0;
	}
	printf("State is now %d\n", state);
}
void sendTimes() {
	/* Function that sends the elasped time to the raspberry pi through the socket server */
	printf("Elapsed time 1:%0.2f\tElapsed time 2: %0.2f\n", elapsedTime, elapsedTime2); // ADDED THIS
	char timeDataBuffer[2][SENSOR_STR_SIZE]; // Buffer to hold formatted time data
	char buffer[2][SENSOR_STR_SIZE]; // Buffer to hold formatted floating-point numbers

	// Format elapsed time data
	snprintf(buffer[0], SENSOR_STR_SIZE, "B%0.2f", elapsedTime2);
	snprintf(buffer[1], SENSOR_STR_SIZE, "%0.2f", elapsedTime);

	// Copy formatted data into timeDataBuffer
	strncpy(timeDataBuffer[0], buffer[0], SENSOR_STR_SIZE);
	strncpy(timeDataBuffer[1], buffer[1], SENSOR_STR_SIZE);

	if (send(client_socket, timeDataBuffer, sizeof(timeDataBuffer), 0) == -1) {
		perror("send");
	}
	printf("Time between message and mission start: %s\n", timeDataBuffer[0]);
	printf("Time elapsed when boat was submerged: %s\n", timeDataBuffer[1]);
}
void sendData(int sockfd, const uint8_t* buffer, size_t bufferSize) {
	/* Function that sends the water quality data to the raspberry pi through the socket server */
	printf("Temperature: %0.2f\tTDS: %0.2f\tpH: %0.2f\tTurbidity: %0.2f\n", temperData[rIndex1], tdsData[rIndex1], pHData[rIndex1], turbData[rIndex1]);
	printf("Temperature: %0.2f\tTDS: %0.2f\tpH: %0.2f\tTurbidity: %0.2f\n", temperData[rIndex2], tdsData[rIndex2], pHData[rIndex2], turbData[rIndex2]);
	sharedTDSValue = (tdsData[rIndex1] + tdsData[rIndex2]) / 2;
	cTemp = (temperData[rIndex1] + temperData[rIndex2]) / 2;
	phValue = (pHData[rIndex1] + pHData[rIndex2]) / 2;
	turbidity = (turbData[rIndex1] + turbData[rIndex2]) / 2;
	snprintf((char*)&dataBuffer[0 * SENSOR_STR_SIZE], SENSOR_STR_SIZE, "C1 %0.2f ", cTemp);
	snprintf((char*)&dataBuffer[1 * SENSOR_STR_SIZE], SENSOR_STR_SIZE, "2 %0.2f ", sharedTDSValue);
	snprintf((char*)&dataBuffer[2 * SENSOR_STR_SIZE], SENSOR_STR_SIZE, "3 %0.2f ", phValue);
	snprintf((char*)&dataBuffer[3 * SENSOR_STR_SIZE], SENSOR_STR_SIZE, "4 %0.2f", turbidity);
	for (size_t i = 0; i < SENSOR_COUNT; i++) {
		const char* str = (const char*)&buffer[i * SENSOR_STR_SIZE];
		size_t strLength = strlen((const char*)&dataBuffer[i * SENSOR_STR_SIZE]);
		dataBuffer[i * SENSOR_STR_SIZE + strLength] = '\0'; // Add null terminator

		ssize_t sent = send(client_socket, str, strLength, 0);
		if (sent < 0) {
			ESP_LOGE(TAG, "Send failed: errno %d", errno);
			break; // Exit if send failed
		}
		// Optional: Delay between sends, if necessary
		vTaskDelay(100 / portTICK_PERIOD_MS);
	}
	for (size_t i = 0; i < SENSOR_COUNT; i++) {
		printf("Sensor %zu: %s\n", i, &dataBuffer[i * SENSOR_STR_SIZE]);
	}
}
void wifi_event_handler(void* event_handler_arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
	/* Handles wifi related events such as connection, disconnection, and timeouts*/
	if (event_id == WIFI_EVENT_STA_START)
	{
		printf("WIFI CONNECTING....\n");
	}
	else if (event_id == WIFI_EVENT_STA_CONNECTED)
	{
		printf("WiFi CONNECTED\n");
	}
	else if (event_id == WIFI_EVENT_STA_DISCONNECTED)
	{
		printf("WiFi lost connection\n");
		if (retry_num < 10) { esp_wifi_connect(); retry_num++; printf("Retrying to Connect...\n"); }
	}
	else if (event_id == IP_EVENT_STA_GOT_IP)
	{
		printf("Wifi got IP...\n\n");
	}
}
void wifi_connection() {
	/* Function to connect to a access point*/
	//                          s1.4
	// 2 - Wi-Fi Configuration Phase
	esp_netif_init();
	esp_event_loop_create_default();     // event loop                    s1.2
	esp_netif_create_default_wifi_sta(); // WiFi station                      s1.3
	wifi_init_config_t wifi_initiation = WIFI_INIT_CONFIG_DEFAULT();
	esp_wifi_init(&wifi_initiation); //
	esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, wifi_event_handler, NULL);
	esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, wifi_event_handler, NULL);
	wifi_config_t wifi_configuration = {
			.sta = {
					.ssid = "",
					.password = "",
				   }
	};
	strcpy((char*)wifi_configuration.sta.ssid, ssid);
	strcpy((char*)wifi_configuration.sta.password, pass);
	//esp_log_write(ESP_LOG_INFO, "Kconfig", "SSID=%s, PASS=%s", ssid, pass);
	esp_wifi_set_config(ESP_IF_WIFI_STA, &wifi_configuration);
	// 3 - Wi-Fi Start Phase
	esp_wifi_start();
	esp_wifi_set_mode(WIFI_MODE_STA);
	// 4- Wi-Fi Connect Phase
	esp_wifi_connect();
	printf("wifi_init_softap finished. SSID:%s  password:%s", ssid, pass);
}
void esp_server_task(void* pvParameter) {
	/* Task that sets up the socket server and manages devices connecting to it*/
	struct sockaddr_in server_address;
	server_address.sin_family = AF_INET;
	server_address.sin_port = htons(PORT_NUMBER);
	server_address.sin_addr.s_addr = htonl(INADDR_ANY);

	int server_socket = socket(AF_INET, SOCK_STREAM, 0);
	if (server_socket < 0) {
		ESP_LOGE(TAG, "Unable to create socket: errno %d", errno);
		vTaskDelete(NULL);
	}

	if (bind(server_socket, (struct sockaddr*)&server_address, sizeof(server_address)) < 0) {
		ESP_LOGE(TAG, "Socket binding failed: errno %d", errno);
		close(server_socket);
		vTaskDelete(NULL);
	}

	if (listen(server_socket, 5) < 0) {
		ESP_LOGE(TAG, "Error during listen: errno %d", errno);
		close(server_socket);
		vTaskDelete(NULL);
	}

	while (1) {
		ESP_LOGI(TAG, "Waiting for connection...");
		client_socket = accept(server_socket, NULL, NULL);
		if (client_socket < 0) {
			ESP_LOGE(TAG, "Accept failed: errno %d", errno);
			if (accept_counter > 5) {
				esp_restart();
			}
			continue;
		}
		printf("Client socket %d\n", client_socket);
		ESP_LOGI(TAG, "Client connected!");
		client_connected = true;
		accept_counter = 0;
		setState();
	}
	close(server_socket); // Close the server socket when server task ends
}
void sendMessage() {
	/* Functon used to send messages to the raspberry pi*/
	const char* message = "";
	if (client_connected) {
		if (processDisrupted) {
			message = "ESP32_Restarted";
			printf("Sent ESP32_Restarted\n");
			processDisrupted = false;
		}
		else if (state == 1) {
			message = "Pre_DC";
			printf("Sent Pre_DC\n");
		}
		else if (state == 2 && SCC_sent) {
			message = "Performing DC";
			printf("Performing DC");
		}
		else if (state == 2) {
			message = "Starting DC";
			printf("Sent Starting DC\n");
			client_connected = false;
			SCC_sent = true;
			//			DC_performed = true;
		}
		else if (state == 3) {
			message = "Post_DC";
			printf("Sending PostDC\n");
		}
		else if (state == 4) {
			printf("Sending times\n");
			sendTimes();
			printf("Sent times\n");
			return;
		}
		else if (state == 5) {
			sendData(client_socket, dataBuffer, sizeof(dataBuffer));
			printf("Sent data\n");
			return;
		}
		int msg_len = strlen(message);
		int bytes_sent = send(client_socket, message, msg_len, 0);
		if (bytes_sent < 0) {
			ESP_LOGE(TAG, "Error sending message to client: errno %d", errno);
			client_connected = false;
		}
		else {
			ESP_LOGI(TAG, "Message sent to client: %s", message);
		}
	}
}
void readMessage(char* buffer, int bufferSize) {
	/* Function that reads messages from the raspberry pi*/
	printf("Reading the message\n");
	char firstCharacter = buffer[0];
	if (strcmp(buffer, "START_COLLECTION") == 0 && !SCM_received) {
		time_DCCreceived = esp_timer_get_time();
		ESP_LOGI(TAG, "Received command to start collection");
		printf("Received command to start collection\n");
		collectData = true;
		SCM_received = true;
	}
	else if (strcmp(buffer, "SEND_ELAPSED_TIMES") == 0) {
		ESP_LOGI(TAG, "Received command to send elapsed times");
		if (!DC_performed) {
			printf("DC not performed can't give elapsed times\n");
			processDisrupted = true;
		}
		else
			STM_received = true;
	}
	else if (firstCharacter == 'T') {
		/* Get the data index time */
		ESP_LOGI(TAG, "Received data indexes collection");
		if (!DC_performed) {
			printf("DC not performed. No data currently collected\n");
		}
		else {
			sscanf(buffer, "T%ld %ld", &rIndex1, &rIndex2);
			DI_received = true;
			printf("These are the indexes: %ld and %ld\n", rIndex1, rIndex2);
		}
	}
	else if (strcmp(buffer, "MISSION_FINISHED") == 0) {
		ESP_LOGI(TAG, "Mission complete");
		SCM_received = false;
		DC_performed = false;
		STM_received = false;
		DI_received = false;
		client_connected = false;
	}
	else {
		printf("Message is unreadable\n");
	}
	setState();
}
void timerCallback(TimerHandle_t xTimer) {
	/* Timer that goes off when a message takes more than 10 seconds to send */
	// Timer has expired, handle timer event here
	if (client_connected) {
		printf("No message received, sending new message\n");
		sendMessage();
	}
	else {
		if (xTimerStop(timerHandle, 0) != pdPASS) {
			printf("Failed to stop timer!\n");
		}
		printf("Client isn't connected. Timer stopped\n");
	}
}
void receiveDataTask(void* pvParameters) {
	/* Task that sends and reads messages from the raspberry pi. It will only attempt
	   these if a client is connected*/
	   // Wait for the socket server to be running
	while (1) {
		while (client_connected) {
			sendMessage();
			char buffer[MAX_DATA_SIZE];
			memset(buffer, 0, sizeof(buffer));
			xTimerStart(timerHandle, 0);
			if (client_connected) {
				int len = recv(client_socket, buffer, sizeof(buffer) - 1, 0); // Wait on RP to send message
				if (len < 0) {
					ESP_LOGE(TAG, "recv failed: errno %d", errno);
					close(client_socket);
					client_connected = false;
					if (xTimerStop(timerHandle, 0) != pdPASS) {
						printf("Failed to stop timer!\n");
					}
					if (xTimerReset(timerHandle, 0) != pdPASS) {
						printf("Failed to reset timer!\n");
					}
					continue;
				}
				readMessage(buffer, MAX_DATA_SIZE);
				printf("Received message: %s\n", buffer);
			}
		}
		vTaskDelay(pdMS_TO_TICKS(100)); // Delay before checking again
	}
}
void ReadWaterData(void* pvParameter) {
	/* Function that records water quality data during data collection procedure*/
	TDS_setup_function();
	PH_setup_function();
	Turbidity_setup_function();
	ds18b20_init(TEMP_BUS);
	ds18b20_setResolution(tempSensors, 2, 12);
	while (1) {
		if (submerged) {
			if (dbIndex == 100)
				dbIndex = 0;
			temperData[dbIndex] = ds18b20_get_temp();
			tdsData[dbIndex] = TDS_function(temperData[dbIndex]);
			pHData[dbIndex] = PH_function(temperData[dbIndex]);
			turbData[dbIndex] = Turbidity_function();
			printf("Data for index %d:", dbIndex);
			printf("Temperature: %0.2f\tTDS: %0.2f\tpH: %0.2f\tTurbidity: %0.2f\n", temperData[dbIndex], tdsData[dbIndex], pHData[dbIndex], turbData[dbIndex]);
			dbIndex++;
		}
		vTaskDelay(200 / portTICK_PERIOD_MS); // Adjust the delay as per your data collection time
	}
}
void liquid_level_task(void* pvParameters) {
	/* Task that determines if WQM is underwater and collects the neceessary elapsed times*/
	esp_rom_gpio_pad_select_gpio(13);
	gpio_set_direction(13, GPIO_MODE_INPUT);

	while (1) {
		int pin_value = gpio_get_level(13);
		if (pin_value == 1 && state == 2 && !submerged) {
			submerged = true;
			time_submerged = esp_timer_get_time();
			elapsedTime2 = (double)(time_submerged - time_DCCreceived) / 1000000;
		}
		else if (pin_value == 0 && submerged && state == 2) {
			time_emerged = esp_timer_get_time();
			elapsedTime = (double)(time_emerged - time_submerged) / 1000000;
			printf("Sensor module is out of the water\n");
			printf("Time passed: %0.2f\n", elapsedTime);
			submerged = false;
			DC_performed = true;
			setState();
		}
		vTaskDelay(pdMS_TO_TICKS(100));
	}
}

void app_main(void) {
	nvs_flash_init();
	wifi_connection();

	// Create the esp_server_task
	if (xTaskCreate(esp_server_task, "esp_server_task", 4096, NULL, 5, NULL) != pdPASS) {
		ESP_LOGE(TAG, "Failed to create esp_server_task");
		return;
	}
	// Create the receiveDataTask
	if (xTaskCreate(receiveDataTask, "receiveDataTask", 4096, NULL, 5, NULL) != pdPASS) {
		ESP_LOGE(TAG, "Failed to create receiveDataTask");
		return;
	}
	// Create the ReadWaterData task
	if (xTaskCreate(ReadWaterData, "ReadWaterData", 4096, NULL, 5, NULL) != pdPASS) {
		ESP_LOGE(TAG, "Failed to create ReadWaterData task");
		return;
	}
	// Create liquid_task
	if (xTaskCreate(liquid_level_task, "liquid_level_task", 4096, NULL, 5, NULL) != pdPASS) {
		ESP_LOGE(TAG, "Failed to create esp_server_task");
		return;
	}
	timerHandle = xTimerCreate("MyTimer", pdMS_TO_TICKS(10000), pdTRUE, 0, timerCallback); // Will change to 10 seconds
}
