#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <dirent.h>
#include <signal.h>
#include <fcntl.h>
#include <sys/types.h>
#include "cJSON/cJSON.h"
#include <assert.h>

#define BUFFER_SIZE 1024
#define NAME_SIZE 32

typedef struct stt_node_t {
    int *value;
    struct stt_node_t *next;
} stt_node_t;

DIR *trace_dir;
stt_node_t *head;
int node_count;

char *trace_dir_path;
int num_var; // number of variable
int *state_id;
int *state_count;

void save_result()
{
    FILE *fp = fopen("probe_transition_result.txt", "w");
    if (!fp) {
        perror("File opening error ");
        exit(EXIT_FAILURE);
    }
    
    char buffer[128] = {0};
    int offset;

    fprintf(fp, "# node\n");
    for (int i = 0; i < node_count; i++) {
        memset(buffer, 0, sizeof(buffer));
        offset = 0;

        for (int j = 0; j < num_var; j++) {
            offset += sprintf(buffer + offset, "%d", head[i].value[j]);
            if (j < num_var - 1) {
                offset += sprintf(buffer + offset, ",");
            }
        }

        fprintf(fp, "%s\n", buffer);
    }

    fprintf(fp, "# transition\n");
    for (int i = 0; i < node_count; i++) {
        stt_node_t *current = head[i].next;
        while (current != NULL) {
            memset(buffer, 0, sizeof(buffer));
            offset = 0;

            for (int j = 0; j < num_var; j++) {
                offset += sprintf(buffer + offset, "%d", head[i].value[j]);
                if (j < num_var - 1) {
                    offset += sprintf(buffer + offset, ",");
                }
            }

            offset += sprintf(buffer + offset, " ");

            for (int j = 0; j < num_var; j++) {
                offset += sprintf(buffer + offset, "%d", current->value[j]);
                if (j < num_var - 1) {
                    offset += sprintf(buffer + offset, ",");
                }
            }

            fprintf(fp, "%s\n", buffer);

            current = current->next;
        }
    }
    
    fclose(fp);
}

// When user press Ctrl+C
void exit_handler(int signal) 
{
    closedir(trace_dir);
    printf("Program stop! Have a nice day!\n");
    
    // save the transition result for graph visualization
    save_result();

    // free or close
    if (trace_dir != NULL) closedir(trace_dir);
    for (int i = 0; i < node_count; i++) {
        if (head[i].value != NULL) free(head[i].value);
    } 
    if (head != NULL) free(head);
    if (trace_dir_path != NULL) free(trace_dir_path);
    if (state_id != NULL) free(state_id);
    if (state_count != NULL) free(state_count);

    exit(EXIT_SUCCESS);
}

void json_parsing(const char *filename) 
{
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        perror("Error opening file ");
        return;
    }

    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);

    // Read the entire file into memory - TODO : Are we sure about this?
    char *json_string = (char *)malloc(file_size + 1);
    if (json_string == NULL) {
        perror("Memory allocation failed ");
        fclose(file);
        return;
    }
    fread(json_string, 1, file_size, file);
    json_string[file_size] = '\0';

    fclose(file);

    // Parse the JSON string
    cJSON *json = cJSON_Parse(json_string);
    if (json == NULL) {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL) {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        free(json_string);
        return;
    }

    // Get values from JSON object
    cJSON *path = cJSON_GetObjectItemCaseSensitive(json, "path");
    cJSON *id = cJSON_GetObjectItemCaseSensitive(json, "id");
    cJSON *vcount = cJSON_GetObjectItemCaseSensitive(json, "vcount");
    cJSON *name = cJSON_GetObjectItemCaseSensitive(json, "name");
    
    if (cJSON_IsString(path) && path->valuestring != NULL) {
        trace_dir_path = (char *)malloc(strlen(path->valuestring) + 1);
        if (trace_dir_path == NULL) {
            perror("Memory allocation failed for trace_dir_path ");
            cJSON_Delete(json);
            free(json_string);
            return;
        }
        strcpy(trace_dir_path, path->valuestring);
        trace_dir_path[strlen(path->valuestring)] = '\0';
    }

    // Get the array size
    if (cJSON_GetArraySize(id) != cJSON_GetArraySize(vcount)) {
        fprintf(stderr, "Array size for 'id' and 'value' should match...\n");
        cJSON_Delete(json);
        free(json_string);
        return;
    }
    num_var = cJSON_GetArraySize(id);

    // Assign parsed data into global variables
    state_id = (int *)malloc(sizeof(int) * num_var);
    if (state_id == NULL) {
        perror("Memory allocation failed for state_id ");
        cJSON_Delete(json);
        free(json_string);
        return;
    }
    state_count = (int *)malloc(sizeof(int) * num_var);
    if (state_count == NULL) {
        perror("Memory allocation failed for state_count ");
        cJSON_Delete(json);
        free(json_string);
        return;
    }

    cJSON *id_element = NULL;
    int i = 0;
    cJSON_ArrayForEach(id_element, id) {
        state_id[i++] = id_element->valueint;        
    }

    i = 0;
    cJSON *vcount_element = NULL;
    cJSON_ArrayForEach(vcount_element, vcount) {
        state_count[i++] = vcount_element->valueint;
    }

    // Free cJSON structure and allocated memory
    cJSON_Delete(json);
    free(json_string);
}

void create_head(stt_node_t *head) 
{
    for (int i = 0; i < node_count; i++) {
        head[i].value = (int *)malloc(sizeof(int) * num_var);
        if (head[i].value == NULL) {
            perror("Memory allocation failed for value ");
            exit(EXIT_FAILURE);
        }
    }

    int* counter = (int *)malloc(sizeof(int) * num_var);
    memset(counter, 0, sizeof(int) * num_var);

    for (int i = 0; i < node_count; i++) {
        for (int j = 0; j < num_var; j++) {
            head[i].value[j] = counter[j];
        }
        counter[num_var-1]++;
        for (int j = num_var-1; j > 0; j--) {
            if (counter[j] >= state_count[j]) {
                counter[j] = 0;
                if (j == 0) {
                    fprintf(stderr, "Logical error: counter overflowed beyond expected range\n");
                    free(counter);
                    exit(EXIT_FAILURE);
                } 
                counter[j-1]++;
            }
        }
    }

    free(counter);
    counter = NULL;
}

stt_node_t *create_node(int *toassign)
{
    stt_node_t *new_node = (stt_node_t *)malloc(sizeof(stt_node_t));
    if (new_node == NULL) {
        perror("Memory allocation failed for creating new node ");
        exit(EXIT_FAILURE);
    }

    new_node->value = (int *)malloc(sizeof(int) * num_var);
    if (new_node->value == NULL) {
        perror("Memory allocation failed for value ");
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < num_var; i++) {
        new_node->value[i] = toassign[i];
    }

    new_node->next = NULL; 
    
    return new_node;
}

void add_edge(int head_idx, stt_node_t *toadd)
{
    stt_node_t *current = &head[head_idx];
    while (current->next != NULL) {
        current = current->next;
    }
    current->next = toadd;
}

int find_head_index(int *value)
{
    int idx = 0;
    int multiplier = 1;
    
    for (int i = num_var-1; i >= 0; i--) {
        idx += value[i] * multiplier;
        if (i > 0) {
            multiplier *= state_count[i];
        }
    }

    return idx;
}

// return 1 if found, return 0 if not found
int find_if_existing(int head_idx, int *tofind)
{
    stt_node_t *current = &head[head_idx];
    while (current != NULL) {
        int match = 0;
        for (int i = 0; i < num_var; i++) {
            if (current->value[i] != tofind[i]) {
                break;
            } else {
                match++;
                if (match == num_var) return 1;
            }
        }
        current = current->next;
    }
    return 0;
}

void open_file() 
{
    trace_dir = opendir(trace_dir_path);
    if(trace_dir == NULL) {
        fprintf(stderr,"Cannot open trace dir %s\n", trace_dir_path);
        exit(EXIT_FAILURE);
    }
    struct dirent *trace_file;
    struct flock file_lock;

    int *cur_val = (int *)malloc(sizeof(int) * num_var);

    // Repeatedly search directory
    while (1) {
        rewinddir(trace_dir);
        while ((trace_file = readdir(trace_dir)) != NULL) {
            if (!strcmp(trace_file->d_name, ".") || !strcmp(trace_file->d_name, "..")) continue;

            char *trace_file_path;
            size_t trace_file_path_len = strlen(trace_dir_path) + strlen(trace_file->d_name) + 2;
            trace_file_path = (char *)malloc(trace_file_path_len);
            if (trace_file_path == NULL) {
                perror("Memory allocation failed for trace_file_path ");
                exit(EXIT_FAILURE);
            }
            // memset(trace_file_path, 0, strlen(trace_file_path));
            strncpy(trace_file_path, trace_dir_path, strlen(trace_dir_path)+1);
            strncat(trace_file_path, "/", sizeof(char));
            strncat(trace_file_path, trace_file->d_name, strlen(trace_file->d_name));
            trace_file_path[trace_file_path_len - 1] = '\0';

            int fd = open(trace_file_path, O_RDWR);
            if (fd == -1) {
                perror("open");
                free(trace_file_path);
                continue;
            }

            // convert file descriptor to FILE *
            FILE *fp = fdopen(fd, "r");
            if (fp == NULL) {
                perror("Error converting file descriptor to FILE * ");
                close(fd);
                free(trace_file_path);
                exit(EXIT_FAILURE);
            }

            file_lock.l_type = F_RDLCK;
            file_lock.l_whence = SEEK_SET;
            file_lock.l_start = 0;
            file_lock.l_len = 0;
            if (fcntl(fd, F_SETLKW, &file_lock) == -1) {
                perror("fcntl");
                close(fd);
                fclose(fp);
                free(trace_file_path);
                continue;
            }

            for (int i = 0; i < num_var; i++) {
                cur_val[i] = 0;
            }
            int temp_id, temp_val, head_idx = 0;    
            while (fscanf(fp, "%d %d", &temp_id, &temp_val) == 2) {
                for (int i = 0; i < num_var; i++) {
                    if (temp_id == state_id[i] && cur_val[i] != temp_val) {
                        cur_val[i] = temp_val;
                        if (find_if_existing(head_idx, cur_val) == 0) {
                            stt_node_t *toadd = create_node(cur_val);
                            add_edge(head_idx, toadd);
                        }
                        head_idx = find_head_index(cur_val);
                        break;
                    }     
                }
            }
            
            file_lock.l_type = F_UNLCK;
            if (fcntl(fd, F_SETLK, &file_lock) == -1) {
                perror("fcntl");
                close(fd);
                fclose(fp);
                free(trace_file_path);
                exit(EXIT_FAILURE);
            }

            close(fd);
            fclose(fp);
            remove(trace_file_path);
            memset(trace_file_path, 0, strlen(trace_file_path));
            free(trace_file_path);
        }
    }

    free(cur_val);
}

int main(int argc, char **argv)
{
    if (argc != 2) {
        printf("Usage: %s <json_file>\n", argv[0]);
        return EXIT_FAILURE;
    }
    const char *json_fn = argv[1];
    
    signal(SIGINT, exit_handler);

    // json parsing
    json_parsing(json_fn);
    
    // create graph (we are using adjacency list)
    node_count = 1;
    for (int i = 0; i < num_var; i++) {
        node_count *= state_count[i];
    }
    
    head = (stt_node_t *)malloc(sizeof(stt_node_t) * node_count);
    if (head == NULL) {
        perror("Memory allocation failed for creating head ");
        exit(EXIT_FAILURE);
    }
    create_head(head);

    // open file and read the state one by one > link them in the adj list
    open_file();

    return 0;
}
