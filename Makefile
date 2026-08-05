.PHONY: dev prod down logs clean db-shell cleanup cron-setup init-ssl deploy

dev:
	docker compose -f docker-compose.dev.yml up -d --build

prod:
	docker compose -f docker-compose.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

logs:
	docker compose logs -f

clean:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down -v
	docker system prune -f

db-shell:
	docker compose exec db psql -U fileshare -d fileshare

cleanup:
	docker compose exec backend python -m app.services.cleanup

cron-setup:
	@crontab -l > mycron || true
	@echo "0 * * * * cd $(shell pwd) && docker compose exec -T backend python -m app.services.cleanup >> /var/log/m3wory-cleanup.log 2>&1" >> mycron
	@crontab mycron
	@rm mycron

init-ssl:
	bash init-letsencrypt.sh

# Команда для удобного деплоя на сервер через SSH (rsync)
# Использование: make deploy HOST=user@ip_address
deploy:
	@if [ -z "$(HOST)" ]; then \
		echo "Ошибка: Укажите HOST (например: make deploy HOST=root@192.168.1.100)"; \
		exit 1; \
	fi
	@echo "Деплой на $(HOST)..."
	rsync -avz --exclude-from='.gitignore' --exclude='.git' ./ $(HOST):~/m3wory-space/
	@echo "Файлы скопированы! Теперь зайдите на сервер и выполните:"
	@echo "ssh $(HOST)"
	@echo "cd ~/m3wory-space"
	@echo "cp .env.example .env # и отредактируйте пароли"
	@echo "make init-ssl # если первый запуск"
	@echo "make prod # для запуска"
