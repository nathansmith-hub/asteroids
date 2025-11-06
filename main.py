# python
import pygame
import sys
from constants import *
from player import Player
from asteroid import Asteroid
from asteroidfield import AsteroidField
from shot import Shot
from logger import log_state, log_event

def main():
    pygame.init()
    print("Starting Asteroids!")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))  # Create window/surface
    clock = pygame.time.Clock()  # Frame timing

    # Sprite groups for update/draw management
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()

    # Register containers for auto-adding new instances
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = updatable
    asteroid_field = AsteroidField()  # Spawns asteroids over time

    Player.containers = (updatable, drawable)
    player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)  # Start at center

    Shot.containers = (shots, updatable, drawable)

    dt = 0  # Delta time (seconds since last frame)
    
    while True:
        # Handle window events (close, etc.)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        
        # Update all game objects with delta time
        updatable.update(dt)

        # Snapshot state ~1/sec to game_state.jsonl
        log_state()

        # Collision checks: player vs asteroids, shots vs asteroids
        for asteroid in asteroids:
            if asteroid.collision(player):
                log_event("player_hit", hp=0)  # Record event of player hit
                print("Game over!")
                sys.exit()
            for shot in shots:
                if asteroid.collision(shot):
                    log_event("shot_hit", asteroid_size=asteroid.radius)  # Record shot impact
                    shot.kill()
                    asteroid.split()

        # Clear screen and draw all visible sprites
        screen.fill("black")
        for i in drawable:
            i.draw(screen)

        pygame.display.flip()  # Present the frame

        # Cap to 60 FPS and compute dt (in seconds)
        dt = clock.tick(60) / 1000

if __name__ == "__main__":
    main()