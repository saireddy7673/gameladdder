import pygame
import cv2
import mediapipe as mp
import random
import time

# Initialize Pygame
pygame.init()
WIDTH, HEIGHT = 600, 700  # Extra height for status text
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snakes and Ladders with Hand Gestures")
clock = pygame.time.Clock()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
GRAY = (150, 150, 150)
BLUE = (0, 0, 255)
fm4KAMibMduFTPf
# Board setup
GRID_SIZE = 10
SQUARE_SIZE = WIDTH // GRID_SIZE
player_pos = 1
paused = False
game_over = False
status_message = "Use gestures: Open hand (roll), Fist (step), Peace (pause)"

# Snakes and Ladders (fixed positions)
snakes = {16: 6, 47: 26, 49: 11, 56: 53, 62: 19, 64: 60, 87: 24, 93: 73, 95: 75, 98: 78}
ladders = {1: 38, 4: 14, 9: 31, 21: 42, 28: 84, 36: 44, 51: 67, 71: 91, 80: 100}

# Initialize Mediapipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# Open webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()


def get_square_coords(pos):
    """Convert board position (1-100) to grid coordinates."""
    row = 9 - ((pos - 1) // GRID_SIZE)  # Bottom to top
    col = (pos - 1) % GRID_SIZE if row % 2 == 0 else 9 - ((pos - 1) % GRID_SIZE)  # Zigzag
    return col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2


def move_player(steps):
    """Move player and handle snakes/ladders."""
    global player_pos, game_over, status_message
    if game_over:
        return
    new_pos = player_pos + steps
    if new_pos <= 100:
        player_pos = new_pos
        # Check ladders
        if player_pos in ladders:
            status_message = f"Ladder! Climbed to {player_pos}"
            player_pos = ladders[player_pos]
        # Check snakes
        if player_pos in snakes:
            status_message = f"Snake! Slid to {player_pos}"
            player_pos = snakes[player_pos]
        if player_pos == 100:
            game_over = True
            status_message = "You Win! Press 'R' to restart."


def detect_gesture(hand_landmarks):
    """Detect hand gestures based on landmarks."""
    if not hand_landmarks:
        return None

    # Key landmarks
    thumb_tip = hand_landmarks.landmark[4]
    index_tip = hand_landmarks.landmark[8]
    middle_tip = hand_landmarks.landmark[12]
    ring_tip = hand_landmarks.landmark[16]
    pinky_tip = hand_landmarks.landmark[20]
    wrist = hand_landmarks.landmark[0]

    # Count raised fingers
    fingers_up = 0
    if index_tip.y < wrist.y: fingers_up += 1
    if middle_tip.y < wrist.y: fingers_up += 1
    if ring_tip.y < wrist.y: fingers_up += 1
    if pinky_tip.y < wrist.y: fingers_up += 1
    if thumb_tip.x > wrist.x if thumb_tip.x < index_tip.x else thumb_tip.x < wrist.x: fingers_up += 1

    # Detect gestures
    if fingers_up == 5:
        return "roll"
    elif fingers_up == 0:
        return "step"
    elif fingers_up == 2 and index_tip.y < wrist.y and middle_tip.y < wrist.y:
        return "pause"
    return None


# Game loop
running = True
last_gesture_time = 0
gesture_cooldown = 1.5  # Seconds between gestures

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and game_over:
            player_pos = 1
            game_over = False
            paused = False
            status_message = "Game restarted!"

    # Fill screen
    screen.fill(BLACK)

    # Draw board
    for i in range(GRID_SIZE):
        for j in range(GRID_SIZE):
            pygame.draw.rect(screen, GRAY, (i * SQUARE_SIZE, j * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE), 1)
            num = (9 - j) * GRID_SIZE + (i + 1 if (9 - j) % 2 == 0 else GRID_SIZE - i)
            font = pygame.font.SysFont(None, 20)
            text = font.render(str(num), True, WHITE)
            screen.blit(text, (i * SQUARE_SIZE + 5, j * SQUARE_SIZE + 5))

    # Draw snakes and ladders
    for start, end in snakes.items():
        start_x, start_y = get_square_coords(start)
        end_x, end_y = get_square_coords(end)
        pygame.draw.line(screen, RED, (start_x, start_y), (end_x, end_y), 3)
    for start, end in ladders.items():
        start_x, start_y = get_square_coords(start)
        end_x, end_y = get_square_coords(end)
        pygame.draw.line(screen, GREEN, (start_x, start_y), (end_x, end_y), 3)

    # Draw player
    if not game_over or player_pos == 100:
        player_x, player_y = get_square_coords(player_pos)
        pygame.draw.circle(screen, BLUE, (player_x, player_y), SQUARE_SIZE // 3)

    # Status text
    font = pygame.font.SysFont(None, 30)
    status_text = font.render(status_message, True, WHITE)
    screen.blit(status_text, (10, HEIGHT - 80))

    # Gesture detection
    ret, frame = cap.read()
    if ret:
        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks and not paused and not game_over:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                gesture = detect_gesture(hand_landmarks)
                current_time = time.time()

                if gesture and (current_time - last_gesture_time > gesture_cooldown):
                    last_gesture_time = current_time
                    if gesture == "roll":
                        steps = random.randint(1, 6)
                        status_message = f"Rolled {steps}"
                        move_player(steps)
                    elif gesture == "step":
                        status_message = "Stepped forward"
                        move_player(1)
                    elif gesture == "pause":
                        paused = True
                        status_message = "Paused - Peace sign to resume"
        elif paused and results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                gesture = detect_gesture(hand_landmarks)
                if gesture == "pause":
                    paused = False
                    status_message = "Resumed"

        cv2.imshow("Hand Gestures", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            running = False

    pygame.display.flip()
    clock.tick(60)

# Cleanup
cap.release()
cv2.destroyAllWindows()
pygame.quit()