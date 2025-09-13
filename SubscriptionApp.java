public package com.example.subscription;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import javax.annotation.PostConstruct;
import java.io.FileInputStream;
import java.io.IOException;
import java.util.*;
import java.util.stream.Collectors;

@SpringBootApplication
@RestController
public class SubscriptionApp {

    // Data storage
    private List<Map<String, String>> userData = new ArrayList<>();
    private List<Map<String, String>> subscriptions = new ArrayList<>();
    private List<Map<String, String>> plans = new ArrayList<>();
    private List<Map<String, String>> logs = new ArrayList<>();
    private List<Map<String, String>> billing = new ArrayList<>();

    public static void main(String[] args) {
        SpringApplication.run(SubscriptionApp.class, args);
    }

    // Load Excel at startup
    @PostConstruct
    public void loadData() throws IOException {
        String filePath = "SubscriptionUseCase_Dataset.xlsx";
        userData = readSheet(filePath, "User_Data");
        subscriptions = readSheet(filePath, "Subscriptions");
        plans = readSheet(filePath, "Subscription_Plans");
        logs = readSheet(filePath, "Subscription_Logs");
        billing = readSheet(filePath, "Billing_Information");
    }

    // Generic Excel reader
    private List<Map<String, String>> readSheet(String filePath, String sheetName) throws IOException {
        List<Map<String, String>> data = new ArrayList<>();
        try (FileInputStream fis = new FileInputStream(filePath);
             Workbook workbook = new XSSFWorkbook(fis)) {

            Sheet sheet = workbook.getSheet(sheetName);
            Iterator<Row> rowIterator = sheet.iterator();

            // Headers
            List<String> headers = new ArrayList<>();
            if (rowIterator.hasNext()) {
                Row headerRow = rowIterator.next();
                headerRow.forEach(cell -> headers.add(cell.getStringCellValue()));
            }

            // Data rows
            while (rowIterator.hasNext()) {
                Row row = rowIterator.next();
                Map<String, String> rowMap = new HashMap<>();
                for (int i = 0; i < headers.size(); i++) {
                    Cell cell = row.getCell(i);
                    String value = (cell == null) ? "" :
                            (cell.getCellType() == CellType.NUMERIC ? String.valueOf(cell.getNumericCellValue()) : cell.getStringCellValue());
                    rowMap.put(headers.get(i), value);
                }
                data.add(rowMap);
            }
        }
        return data;
    }

    // API: Recommend plans
    @GetMapping("/recommend/{userId}")
    public Object recommendPlans(@PathVariable String userId) {
        Optional<Map<String, String>> userOpt = userData.stream()
                .filter(u -> u.get("User Id").equals(userId))
                .findFirst();

        if (!userOpt.isPresent()) {
            return Collections.singletonMap("error", "User ID not found.");
        }

        // Active subscriptions
        List<Map<String, String>> userSubs = subscriptions.stream()
                .filter(s -> s.get("User Id").equals(userId)
                        && s.get("Status").equalsIgnoreCase("active"))
                .collect(Collectors.toList());

        if (userSubs.isEmpty()) {
            // If no active subs → recommend cheapest 3
            return plans.stream()
                    .sorted(Comparator.comparingDouble(p -> Double.parseDouble(p.get("Price"))))
                    .limit(3)
                    .collect(Collectors.toList());
        }

        // Get user's average price and auto-renew preference
        List<Map<String, String>> userPlans = plans.stream()
                .filter(p -> userSubs.stream()
                        .anyMatch(s -> s.get("Product Id").equals(p.get("Product Id"))))
                .collect(Collectors.toList());

        double avgPrice = userPlans.stream()
                .mapToDouble(p -> Double.parseDouble(p.get("Price")))
                .average()
                .orElse(0);

        double avgAutoRenew = userPlans.stream()
                .mapToInt(p -> p.get("Auto Renewal Allowed").equalsIgnoreCase("Yes") ? 1 : 0)
                .average()
                .orElse(0);

        // Run simple KNN: Find closest 3 plans
        List<Map<String, Object>> scoredPlans = new ArrayList<>();
        for (Map<String, String> p : plans) {
            double price = Double.parseDouble(p.get("Price"));
            int autoRenew = p.get("Auto Renewal Allowed").equalsIgnoreCase("Yes") ? 1 : 0;
            double distance = Math.sqrt(Math.pow(price - avgPrice, 2) + Math.pow(autoRenew - avgAutoRenew, 2));

            Map<String, Object> scored = new HashMap<>(p);
            scored.put("distance", distance);
            scoredPlans.add(scored);
        }

        return scoredPlans.stream()
                .sorted(Comparator.comparingDouble(p -> (Double) p.get("distance")))
                .limit(3)
                .collect(Collectors.toList());
    }
}
 {
    
}
